"""
AG-UI (Agent-User Interaction Protocol) 核心协议实现
为 MemeMorph 提供流式 SSE 事件生命周期调度、Frontend Tools 调用契约与 Human-in-the-Loop (HITL) 质检挂起恢复机制。
"""

import json
import time
import uuid
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from fastapi.responses import StreamingResponse

class AGUIEventType(str, Enum):
    RUN_STARTED = "RUN_STARTED"
    STEP_STARTED = "STEP_STARTED"
    STEP_FINISHED = "STEP_FINISHED"
    TEXT_MESSAGE_CHUNK = "TEXT_MESSAGE_CHUNK"
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_RESULT = "TOOL_CALL_RESULT"
    INPUT_REQUEST = "INPUT_REQUEST"      # HITL: 请求人类裁决或输入
    INPUT_RESPONSE = "INPUT_RESPONSE"    # HITL: 用户决策已收到
    STATE_SNAPSHOT = "STATE_SNAPSHOT"
    RUN_FINISHED = "RUN_FINISHED"
    RUN_ERROR = "RUN_ERROR"

@dataclass
class AGUIEvent:
    type: AGUIEventType
    payload: Dict[str, Any]
    run_id: str
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)

    def to_sse(self) -> str:
        """转换为标准 Server-Sent Events 文本帧"""
        data = {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "type": self.type.value if isinstance(self.type, AGUIEventType) else str(self.type),
            "timestamp": self.timestamp,
            "payload": self.payload
        }
        return f"event: ag-ui-event\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

class HITLManager:
    """人机协同中断管理器，用于在协程中暂停等待用户在前端交互"""
    def __init__(self):
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop and self._loop.is_running():
            return self._loop
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.get_event_loop()

    async def wait_for_human(self, request_id: str, timeout: float = 300.0) -> Dict[str, Any]:
        loop = self.get_loop()
        future = loop.create_future()
        self._pending_requests[request_id] = future
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            # 超时返回默认策略（防止任务永久卡死）
            return {"action": "timeout_default", "decision": "auto_approve", "timed_out": True}
        finally:
            self._pending_requests.pop(request_id, None)

    def resolve_human_input(self, request_id: str, user_response: Dict[str, Any]) -> bool:
        future = self._pending_requests.get(request_id)
        if future and not future.done():
            loop = self.get_loop()
            if loop.is_running():
                loop.call_soon_threadsafe(future.set_result, user_response)
            else:
                future.set_result(user_response)
            return True
        return False

class AGUIEventManager:
    """AG-UI 任务事件队列调度器"""
    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._event_history: Dict[str, list] = {}  # 保存近期事件，防止前端晚连接漏听
        self.hitl = HITLManager()

    def get_or_create_queue(self, run_id: str) -> asyncio.Queue:
        if run_id not in self._queues:
            self._queues[run_id] = asyncio.Queue()
        return self._queues[run_id]

    async def emit(self, run_id: str, event_type: AGUIEventType, payload: Dict[str, Any]):
        queue = self.get_or_create_queue(run_id)
        event = AGUIEvent(type=event_type, payload=payload, run_id=run_id)
        if run_id not in self._event_history:
            self._event_history[run_id] = []
        self._event_history[run_id].append(event)
        await queue.put(event)

    def emit_nowait(self, run_id: str, event_type: AGUIEventType, payload: Dict[str, Any]):
        queue = self.get_or_create_queue(run_id)
        event = AGUIEvent(type=event_type, payload=payload, run_id=run_id)
        if run_id not in self._event_history:
            self._event_history[run_id] = []
        self._event_history[run_id].append(event)
        queue.put_nowait(event)

    async def sse_generator(self, run_id: str) -> AsyncGenerator[str, None]:
        queue = self.get_or_create_queue(run_id)

        # 1. 补发历史事件（如果前端刚建立 SSE 连接）
        history = self._event_history.get(run_id, [])
        for past_event in history:
            yield past_event.to_sse()
            if past_event.type in (AGUIEventType.RUN_FINISHED, AGUIEventType.RUN_ERROR):
                return

        # 2. 持续监听新事件
        try:
            while True:
                try:
                    event: AGUIEvent = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield event.to_sse()
                    if event.type in (AGUIEventType.RUN_FINISHED, AGUIEventType.RUN_ERROR):
                        break
                except asyncio.TimeoutError:
                    # 心跳保持连接
                    yield ": keep-alive ping\n\n"
        finally:
            pass

# 全局单例管理器
global_ag_ui_manager = AGUIEventManager()

def create_ag_ui_stream_response(run_id: str) -> StreamingResponse:
    return StreamingResponse(
        global_ag_ui_manager.sse_generator(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
