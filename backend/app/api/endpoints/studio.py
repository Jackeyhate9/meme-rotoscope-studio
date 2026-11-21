from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import time
import asyncio
import json
from datetime import datetime, timedelta

from app.services.scene_detector import SceneDetectorService
from app.services.qc_agent import VideoQCAgent
from app.services.search_service import SearchService
from app.services.storage_manager import StorageManager
from app.services.hypit_engine import HypitEngineService
from app.services.cloud_engines import EngineGateway
from app.core.ag_ui import global_ag_ui_manager, AGUIEventType, create_ag_ui_stream_response

router = APIRouter()

# 运行时内存任务缓存
TASKS_DB: Dict[str, Dict[str, Any]] = {}

# ------------------ 请求模型 ------------------
class SearchQuery(BaseModel):
    keyword: str = ""
    category: str = "全部"
    limit: int = 8

class AnalyzeRequest(BaseModel):
    video_url: str
    long_video_mode: Optional[bool] = False

class GenerateRequest(BaseModel):
    video_url: str
    target_character: str
    prompt: str
    engine: str = "SEED 2.5"
    auto_qc: bool = True
    interactive_qc: bool = False
    long_video_mode: Optional[bool] = False

class AGUIInputRequest(BaseModel):
    action: str  # "human_decision" 或 "tool_result"
    request_id: Optional[str] = None
    decision: Optional[str] = None  # "approve" 或 "reroll"
    call_id: Optional[str] = None
    status: Optional[str] = "success"
    result: Optional[Any] = None
    data: Optional[Dict[str, Any]] = None

class AgentChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class RerollRequest(BaseModel):
    shot_id: int

class CustomCharacterRequest(BaseModel):
    name: str
    tag: Optional[str] = "自选"
    prompt: Optional[str] = ""
    avatar_url: Optional[str] = None

class RechargeRequest(BaseModel):
    package_name: str
    credits: int
    amount: str

class TakedownRequest(BaseModel):
    video_url: str
    description: str
    contact: str

class ApiApplyRequest(BaseModel):
    email: str
    company: Optional[str] = ""

# ------------------ 后台异步渲染流水线 (AG-UI 增强型 + Hypit 本地引擎 + 一键长视频修改) ------------------
async def mock_render_pipeline(task_id: str, shots: List[Dict[str, Any]], character: str, video_url: str, prompt: str, interactive_qc: bool = False, engine: str = "SEED 2.5", long_video_mode: bool = False):
    """
    后台异步渲染流转任务，支持调度本地 Hypit (FastVideo v2 / H3) 或云端引擎，集成 AG-UI 全双工流式推送与 HITL 质检。
    """
    # 0. 路由分发：若选择本地 Hypit 引擎，直接执行工业级本地 FastVideo/H3 流程
    if "hypit" in engine.lower():
        result = await HypitEngineService.run_pipeline(
            task_id=task_id,
            video_url=video_url,
            character_name=character,
            prompt=prompt,
            shots=shots,
            event_manager=global_ag_ui_manager,
            interactive_qc=interactive_qc,
            long_video_mode=long_video_mode
        )
        shots_data = result["shots"]
        qc_result = result["qc_summary"]
        project_record = {
            "id": task_id,
            "title": f"作品交付：《{character} 二创热门舞台》 (Hypit 一键长视频版)" if long_video_mode else f"作品交付：《{character} 二创热门舞台》 (Hypit 本地超清版)",
            "character": character,
            "prompt": prompt,
            "video_url": video_url,
            "engine": engine,
            "cover_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=800&auto=format&fit=crop",
            "result_url": result["result_url"],
            "shots_count": len(shots_data),
            "duration_sec": round(len(shots_data) * 5.0, 1),
            "credits_cost": 45,
            "created_at": datetime.now().isoformat(),
            "status": "completed",
            "qc_score": qc_result.get("overall_score", 9.5),
            "shots": shots_data,
            "hypit_plan": result.get("hypit_plan")
        }
        StorageManager.save_project(project_record)
        if task_id in TASKS_DB:
            TASKS_DB[task_id]["progress"] = 100
            TASKS_DB[task_id]["status"] = "completed"
            TASKS_DB[task_id]["current_step"] = "Hypit FastVideo 本地渲染完成，原声音轨缝合交付！"
            TASKS_DB[task_id]["result_url"] = result["result_url"]
            TASKS_DB[task_id]["qc_summary"] = qc_result
            TASKS_DB[task_id]["shots"] = shots_data
            TASKS_DB[task_id]["project"] = project_record
        await global_ag_ui_manager.emit(task_id, AGUIEventType.RUN_FINISHED, {
            "task_id": task_id,
            "result_url": result["result_url"],
            "qc_summary": qc_result,
            "shots": shots_data,
            "project": project_record,
            "message": "Hypit 本地二创成片已交付！"
        })
        return

    # 1. 云端/通用多模态模型流水线
    await global_ag_ui_manager.emit(task_id, AGUIEventType.RUN_STARTED, {
        "task_id": task_id,
        "character": character,
        "prompt": prompt,
        "shots_count": len(shots),
        "message": "AG-UI 渲染集群已分配，启动全链路工业化流水线..."
    })

    # 步骤 1: SAM 2 遮罩跟踪
    await global_ag_ui_manager.emit(task_id, AGUIEventType.STEP_STARTED, {
        "step_name": "SAM 2 主角动态跟踪与 Mask 提取",
        "progress": 35,
        "shot_count": len(shots)
    })
    await asyncio.sleep(1.2)
    if task_id in TASKS_DB:
        TASKS_DB[task_id]["status"] = "processing"
        TASKS_DB[task_id]["progress"] = 35
        TASKS_DB[task_id]["current_step"] = "SAM 2 主角动态跟踪与 Mask 提取完成..."
    await global_ag_ui_manager.emit(task_id, AGUIEventType.STEP_FINISHED, {
        "step_name": "SAM 2 跟踪完成",
        "mask_count": 450,
        "background_preserved": True
    })

    # 步骤 2: 核心引擎渲染 (动态调度 Seedance / Kling / MiniMax / 自定义云端底座)
    eng_lower = (engine or "").lower()
    if "kling" in eng_lower or "kline" in eng_lower:
        engine_display = "Kuaishou Kling AI (可灵电影版)"
        render_step_desc = "Kling 1.5 电影级光影物理重绘中 (自回归流体与布料解算)..."
    elif "seed" in eng_lower or "byte" in eng_lower:
        engine_display = "ByteDance Seedance (SEED 2.5)"
        render_step_desc = "Seedance 2.5 字节高保真多模态姿态迁移渲染中..."
    elif "minimax" in eng_lower:
        engine_display = "MiniMax Video-01 (海螺)"
        render_step_desc = "MiniMax Video-01 大幅度肢体动力学渲染中..."
    else:
        engine_display = engine
        render_step_desc = f"{engine} 并行渲染第 2/3 分镜中..."

    await global_ag_ui_manager.emit(task_id, AGUIEventType.STEP_STARTED, {
        "step_name": render_step_desc,
        "progress": 70,
        "engine": engine_display
    })
    await asyncio.sleep(1.5)
    if task_id in TASKS_DB:
        TASKS_DB[task_id]["progress"] = 70
        TASKS_DB[task_id]["current_step"] = render_step_desc
    await global_ag_ui_manager.emit(task_id, AGUIEventType.STEP_FINISHED, {
        "step_name": f"{engine_display} 分镜扩散渲染完成",
        "engine": engine_display
    })

    # 步骤 3: 质检阶段 (Auto-QC)
    qc_result = VideoQCAgent.inspect_shot("mock_shot.mp4", character, interactive_qc=interactive_qc)
    await global_ag_ui_manager.emit(task_id, AGUIEventType.STEP_STARTED, {
        "step_name": "Auto-QC 视觉多维质检评估",
        "progress": 85,
        "qc_score": qc_result.get("overall_score", 9.4),
        "details": qc_result.get("details", {})
    })
    await asyncio.sleep(0.8)

    # 人机协同 (HITL) 中断交互：若开启了交互质检或评分低于 7.5，挂起协程并向前端推送裁决请求
    if qc_result.get("requires_hitl"):
        req_id = f"hitl_{uuid.uuid4().hex[:8]}"
        await global_ag_ui_manager.emit(task_id, AGUIEventType.INPUT_REQUEST, {
            "request_id": req_id,
            "task_id": task_id,
            "shot_id": 2,
            "prompt": "分镜 02 检测到局部动作形变（评分 7.4），已发起人机协同裁决",
            "score": qc_result.get("overall_score", 7.4),
            "details": qc_result.get("details", {}),
            "options": ["通过并合成", "免费重抽此镜头"]
        })
        # 异步等待前端用户选择，超时 15 秒自动通过
        hitl_res = await global_ag_ui_manager.hitl.wait_for_human(req_id, timeout=15.0)
        user_decision = hitl_res.get("decision", "approve")
        if user_decision == "reroll":
            await global_ag_ui_manager.emit(task_id, AGUIEventType.STEP_STARTED, {
                "step_name": "分镜 02 响应用户指令免费重抽微调中...",
                "progress": 90
            })
            await asyncio.sleep(1.0)
            qc_result["overall_score"] = 9.8
            qc_result["verdict"] = "单镜头重抽完成，评分提升至 9.8！"
            await global_ag_ui_manager.emit(task_id, AGUIEventType.STEP_FINISHED, {
                "step_name": "镜头 02 重抽成功",
                "new_score": 9.8
            })

    shots_data = [
        {
            "shot_id": 1,
            "title": "镜头 01 (近景面部置换)",
            "time_range": "00:00 - 00:04",
            "status": "质检通过 (9.4)",
            "image_url": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=400&auto=format&fit=crop"
        },
        {
            "shot_id": 2,
            "title": "镜头 02 (全身肢体卡点)",
            "time_range": "00:04 - 00:09",
            "status": f"质检通过 ({qc_result.get('overall_score', 9.2)})",
            "image_url": "https://images.unsplash.com/photo-1547153760-18fc86324498?q=80&w=400&auto=format&fit=crop"
        },
        {
            "shot_id": 3,
            "title": "镜头 03 (舞台定格伴舞)",
            "time_range": "00:09 - 00:15",
            "status": "质检通过 (9.6)",
            "image_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=400&auto=format&fit=crop"
        }
    ]

    project_record = {
        "id": task_id,
        "title": f"作品交付：《{character} 二创热门舞台》 (15s 高清完整版)",
        "character": character,
        "prompt": prompt,
        "video_url": video_url,
        "cover_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=800&auto=format&fit=crop",
        "result_url": "https://assets.mememorph.ai/demo_result_1080p.mp4",
        "shots_count": len(shots_data),
        "duration_sec": 14.8,
        "credits_cost": 45,
        "created_at": datetime.now().isoformat(),
        "status": "completed",
        "qc_score": qc_result.get("overall_score", 9.4),
        "shots": shots_data
    }

    # 持久化存储到用户历史项目中 (赋予 30 天有效期)
    StorageManager.save_project(project_record)

    if task_id in TASKS_DB:
        TASKS_DB[task_id]["progress"] = 100
        TASKS_DB[task_id]["status"] = "completed"
        TASKS_DB[task_id]["current_step"] = "质检通过，成片缝合完成！"
        TASKS_DB[task_id]["result_url"] = "https://assets.mememorph.ai/demo_result_1080p.mp4"
        TASKS_DB[task_id]["qc_summary"] = qc_result
        TASKS_DB[task_id]["shots"] = shots_data
        TASKS_DB[task_id]["project"] = project_record

    # 4. 发送终态完成事件
    await global_ag_ui_manager.emit(task_id, AGUIEventType.RUN_FINISHED, {
        "task_id": task_id,
        "result_url": "https://assets.mememorph.ai/demo_result_1080p.mp4",
        "qc_summary": qc_result,
        "shots": shots_data,
        "project": project_record,
        "message": "成片缝合完成！"
    })

# ------------------ 搜索与灵感广场端点 ------------------
@router.get("/search")
def search_videos(keyword: str = "", category: str = "全部", limit: int = 8):
    """
    后端多源搜索：支持 B站 实时爬虫检索与热门二创模版库检索，同步到前端
    """
    items = SearchService.search_videos(keyword=keyword, category=category, limit=limit)
    return {
        "status": "success",
        "keyword": keyword,
        "category": category,
        "total": len(items),
        "items": items
    }

@router.get("/explore")
def get_explore_feed():
    """
    获取灵感广场首页数据：推荐卡片、分类、跑马灯与风云榜
    """
    templates = SearchService.search_videos("", category="全部", limit=6)
    return {
        "status": "success",
        "marquee_news": [
            {"time": "2分钟前", "user": "UP主*老铁", "text": "导出了 1080P《范德彪女团Supernova卡点舞》"},
            {"time": "5分钟前", "user": "用户_9921", "text": "制作了《赵本山太空步 × 机械锁舞》质检评分 9.8"},
            {"time": "8分钟前", "user": "晋西北剪辑", "text": "导出了《李云龙 & 楚云飞双人拉丁舞》"},
            {"time": "11分钟前", "user": "赛博小道童", "text": "体验了《大红棉袄变身赛博朋克舞》"}
        ],
        "top_leaderboard": [
            {"rank": 1, "title": "范德彪女团卡点舞", "heat": "B站热度 98.4w", "trend": "+142% ↑", "character": "范德彪", "template_tag": "kpop_aespa"},
            {"rank": 2, "title": "赵本山开原大舞厅太空步", "heat": "抖音热度 84.1w", "trend": "+98% ↑", "character": "赵本山", "template_tag": "lock_dance"},
            {"rank": 3, "title": "平安县城双人拉丁：老李与楚兄", "heat": "B站热度 62.9w", "trend": "+65% ↑", "character": "李云龙", "template_tag": "latin_duo"},
            {"rank": 4, "title": "东北药匣子自制说唱 MV", "heat": "播放 41.5w", "trend": "+38% ↑", "character": "东北药匣子", "template_tag": "yaoxiazirap"}
        ],
        "templates": templates
    }

# ------------------ 视频分析端点 ------------------
@router.post("/analyze")
def analyze_video(req: AnalyzeRequest):
    """
    分析视频：自动检测镜头分镜（支持 15s 短剧卡点与 60s 一键长视频修改），并返回 AI 大脑推荐的反差二创方案
    """
    shots = SceneDetectorService.detect_scenes(req.video_url, long_video_mode=req.long_video_mode)
    duration_sec = 60.0 if req.long_video_mode else 14.8
    
    # 动态根据视频链接或关键词生成方案
    char_a = "范德彪"
    char_b = "赵本山"
    if "lock" in req.video_url.lower() or "机械" in req.video_url:
        char_a, char_b = "赵本山", "范德彪"
    elif "latin" in req.video_url.lower() or "双人" in req.video_url:
        char_a, char_b = "李云龙", "楚云飞"

    ideas = [
        {
            "title": f"方案 A: 【{char_a}】顶流卡点打歌",
            "character": char_a,
            "prompt": f"反差开原风：{char_a}身穿维多利亚西装，神情霸气跳 K-Pop 卡点女团舞，保留招牌手势与冷峻神态",
            "tag": "爆款推荐"
        },
        {
            "title": f"方案 B: 【{char_b}】开原大剧院特别版",
            "character": char_b,
            "prompt": f"全员复古：身穿绿色雷锋棉袄、皮草雷锋帽，雪地舞台光效，背景出现二人转秧歌红绸",
            "tag": "高反差"
        }
    ]

    if req.long_video_mode:
        ideas.append({
            "title": f"方案 C: 【一键长视频全片修改】{char_a} 完整 MV 连续姿态迁移",
            "character": char_a,
            "prompt": f"Hypit 全局长视频连贯转绘：保持 60s 完整 MV 节奏，原声音轨无损合流，消除时序闪烁",
            "tag": "长视频特权"
        })

    return {
        "status": "success",
        "video_duration_sec": duration_sec,
        "shots_count": len(shots),
        "long_video_mode": req.long_video_mode,
        "shots": shots,
        "recommended_ideas": ideas
    }

# ------------------ 生成任务端点 ------------------
@router.post("/generate")
def create_generation_task(req: GenerateRequest, background_tasks: BackgroundTasks):
    """
    提交二创任务，扣除 45 算力，启动异步生成流水线 (支持短卡点与一键长视频修改)
    """
    user = StorageManager.get_user_profile()
    if user.get("credits", 0) < 45:
        raise HTTPException(status_code=400, detail="算力不足，请先在收银台充值！")

    # 扣除算力
    remaining_credits = StorageManager.update_credits(-45)

    task_id = f"task_{uuid.uuid4().hex[:12]}"
    shots = SceneDetectorService.detect_scenes(req.video_url, long_video_mode=req.long_video_mode)
    
    TASKS_DB[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "progress": 5,
        "current_step": "排队就绪，已分配 GPU 节点 (支持一键长视频修改与 Hypit 引擎)...",
        "shots": shots,
        "character": req.target_character,
        "long_video_mode": req.long_video_mode,
        "created_at": time.time()
    }
    
    background_tasks.add_task(
        mock_render_pipeline,
        task_id,
        shots,
        req.target_character,
        req.video_url,
        req.prompt,
        req.interactive_qc,
        req.engine,
        req.long_video_mode
    )
    
    return {
        "status": "success",
        "task_id": task_id,
        "credits_deducted": 45,
        "remaining_credits": remaining_credits,
        "engine": req.engine,
        "ag_ui_stream_url": f"/api/v1/studio/task/{task_id}/ag-ui-stream",
        "message": "二创任务已提交，后台 GPU 集群正在切片渲染中"
    }

@router.get("/task/{task_id}")
def get_task_status(task_id: str):
    """
    传统轮询端点：查询任务生成进度 (提供向后兼容)
    """
    if task_id not in TASKS_DB:
        raise HTTPException(status_code=404, detail="Task not found")
    return TASKS_DB[task_id]

@router.get("/hypit/status")
def get_hypit_status():
    """
    检查本地 Hypit 生产底座环境就绪状态、ComfyUI 端口与显存配置
    """
    return HypitEngineService.get_runtime_status()

class EngineTestRequest(BaseModel):
    engine_id: str

@router.get("/engines/status")
def get_engines_matrix_status():
    """
    检查全量多模态视频大模型与本地引擎矩阵 (Seedance, Kling/Kline, MiniMax, Hypit) 状态与接入能力
    """
    return {
        "status": "success",
        "engines": EngineGateway.get_engines_matrix(),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/engines/test")
def test_engine_connection(req: EngineTestRequest):
    """
    测试单个引擎连接可用性与密钥状态
    """
    return EngineGateway.test_engine_connection(req.engine_id)

# ------------------ AG-UI 协议标准核心端点 ------------------
@router.get("/task/{task_id}/ag-ui-stream")
async def get_ag_ui_task_stream(task_id: str):
    """
    AG-UI 协议标准 Server-Sent Events 流式端点
    前端 EventSource 连接后实时接收 RUN_STARTED / STEP_STARTED / INPUT_REQUEST / RUN_FINISHED 事件
    """
    return create_ag_ui_stream_response(task_id)

@router.post("/task/{task_id}/ag-ui-input")
async def handle_ag_ui_input(task_id: str, req: AGUIInputRequest):
    """
    AG-UI 双向控制通道：接收人机协同 (HITL) 决策中断裁决或前端工具调用 (Frontend Tools) 执行结果
    """
    if req.action == "human_decision" and req.request_id:
        resolved = global_ag_ui_manager.hitl.resolve_human_input(req.request_id, {
            "action": req.action,
            "decision": req.decision or "approve",
            "data": req.data or {}
        })
        return {
            "status": "success",
            "message": f"HITL 决策已接收并恢复流水线执行 (resolved={resolved})",
            "decision": req.decision
        }
    elif req.action == "tool_result":
        return {
            "status": "success",
            "call_id": req.call_id,
            "message": "前端工具调用结果已记录"
        }
    return {"status": "ignored"}

@router.post("/agent/chat")
async def agent_copilot_chat(req: AgentChatRequest):
    """
    AG-UI 驱动的 AI 创意领航员：支持流式打字与前端工具 (Frontend Tools) 调度无限画布与 Hypit 本地引擎
    """
    async def chat_stream():
        user_text = req.message.strip().lower()
        is_hypit = any(kw in user_text for kw in ["hypit", "本地", "fastvideo", "免算力", "零成本", "显存", "离线", "pika"])
        should_add_branch = any(kw in user_text for kw in ["分支", "派生", "创建", "加个", "再来", "对比", "赵本山", "李云龙", "范德彪"])
        target_char = "赵本山" if "本山" in user_text else ("李云龙" if "李云龙" in user_text else "范德彪")
        target_engine = "Local Hypit (FastVideo v2)" if is_hypit else "MiniMax 海螺 H3"

        if is_hypit:
            reply_intro = f"收到指令！AI 领航员已锁定本地 Hypit 生产底座 (FastVideo v2 · 6步加速)，正在规划 5s 分镜与原片光影保持参数..."
        else:
            reply_intro = f"收到指令！AI 领航员正在基于原视频进行反差节奏推演..."

        yield f"event: ag-ui-event\ndata: {json.dumps({'type': 'TEXT_MESSAGE_CHUNK', 'payload': {'delta': reply_intro}})}\n\n"
        await asyncio.sleep(0.4)

        if should_add_branch:
            # 触发前端工具调用：create_canvas_branch
            tool_payload = {
                "call_id": f"call_{uuid.uuid4().hex[:8]}",
                "tool_name": "create_canvas_branch",
                "args": {
                    "character_name": target_char,
                    "engine": target_engine,
                    "prompt": f"反差开原风：{target_char}身穿标志性服饰，跟随女团快节奏卡点反差爆笑舞"
                }
            }
            yield f"event: ag-ui-event\ndata: {json.dumps({'type': 'TOOL_CALL_START', 'payload': tool_payload})}\n\n"
            await asyncio.sleep(0.5)

            if is_hypit:
                followup = (
                    f"\n\n⚡ **AG-UI 前端工具已执行**：\n"
                    f"- 已在无限画布自动派生【{target_char}】分支，引擎绑定为 **Local Hypit (FastVideo v2)**；\n"
                    f"- 启用 **lightingMode='source'**，舞台灯光、彩色射灯与伴舞 100% 保持；\n"
                    f"- 启用 Windows GPU 锁与 22,000MiB 显存门禁，**本地零 API 采购算力**！"
                )
            else:
                followup = f"\n\n✨ **AG-UI 前端工具已执行**：已在您的无限画布上自动派生了【{target_char}】的新分支，并接通了脉冲贝塞尔数据流线！您可随时在画布上双击或对比预览。"
            yield f"event: ag-ui-event\ndata: {json.dumps({'type': 'TEXT_MESSAGE_CHUNK', 'payload': {'delta': followup}})}\n\n"
        elif is_hypit:
            # 切换当前工坊的主渲染引擎为 Hypit
            tool_payload = {
                "call_id": f"call_{uuid.uuid4().hex[:8]}",
                "tool_name": "set_render_engine",
                "args": { "engine": "Local Hypit (FastVideo v2)" }
            }
            yield f"event: ag-ui-event\ndata: {json.dumps({'type': 'TOOL_CALL_START', 'payload': tool_payload})}\n\n"
            followup = "\n\n⚡ **AG-UI 前端工具已执行**：已将当前工坊的主渲染引擎无缝切换至 **Local Hypit (FastVideo v2)**！"
            yield f"event: ag-ui-event\ndata: {json.dumps({'type': 'TEXT_MESSAGE_CHUNK', 'payload': {'delta': followup}})}\n\n"
        else:
            analysis = (
                f"\n\n📊 **原片爆款潜力分析报告**：\n"
                f"- **卡点节奏契合度**：9.6 分（前 15s 包含 3 处重低音变奏，极易产生反差张力）。\n"
                f"- **推荐二创角色**：范德彪（开原第一狠人霸气打歌） / 赵本山（大舞厅太空步）。\n"
                f"- **防崩坏策略**：建议勾选 SAM 2 绿色目标追踪或调度本地 Hypit (FastVideo v2) 开启 source 光影保持。"
            )
            yield f"event: ag-ui-event\ndata: {json.dumps({'type': 'TEXT_MESSAGE_CHUNK', 'payload': {'delta': analysis}})}\n\n"

        yield f"event: ag-ui-event\ndata: {json.dumps({'type': 'RUN_FINISHED', 'payload': {'status': 'completed'}})}\n\n"

    return StreamingResponse(
        chat_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )

@router.post("/task/{task_id}/reroll-shot")
def reroll_single_shot(task_id: str, req: RerollRequest):
    """
    单镜头独立重抽：扣除 10 算力，触发 Auto-QC 重审并微调镜头
    """
    user = StorageManager.get_user_profile()
    if user.get("credits", 0) < 10:
        raise HTTPException(status_code=400, detail="算力不足，无法单独重抽！")

    remaining_credits = StorageManager.update_credits(-10)
    qc_result = VideoQCAgent.inspect_shot(f"shot_{req.shot_id}.mp4", "target")

    return {
        "status": "success",
        "shot_id": req.shot_id,
        "credits_deducted": 10,
        "remaining_credits": remaining_credits,
        "new_status": "质检通过 (9.8 升级)",
        "qc_summary": qc_result,
        "message": f"镜头 0{req.shot_id} 单独重抽成功，已微调面部骨骼特征！"
    }

# ------------------ 项目生命周期与一键替换淘汰端点 ------------------
@router.get("/projects")
def list_projects():
    """
    获取用户所有历史作品，包含有效期（一般为1个月）计算。
    超过30天的老项目，其“一键替换”功能自动淘汰（can_replace = False）。
    """
    projects = StorageManager.get_projects()
    active_count = sum(1 for p in projects if not p.get("is_expired"))
    expired_count = sum(1 for p in projects if p.get("is_expired"))

    return {
        "status": "success",
        "total": len(projects),
        "active_count": active_count,
        "expired_count": expired_count,
        "validity_policy": "项目生成后享有 30 天（1个月）一键替换有效期；超过 30 天后一键替换功能自动淘汰释放，成片仍可归档下载，防止界面无休止堆积。",
        "projects": projects
    }

@router.delete("/projects/{project_id}")
def delete_project(project_id: str):
    """
    删除单个项目
    """
    success = StorageManager.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="项目不存在或已被删除")
    return {"status": "success", "message": "项目已删除"}

@router.post("/projects/clean-expired")
def clean_expired_projects():
    """
    一键清理淘汰已过期的老项目（>30天），
    彻底解决前端界面堆积越来越多的问题！
    """
    result = StorageManager.clean_expired_projects()
    return {
        "status": "success",
        "data": result
    }

@router.post("/projects/simulate-expire")
def simulate_expired_project(days_ago: int = 35):
    """
    测试辅助接口：快速注入一个35天前的老项目，用于直观验证一键替换淘汰功能
    """
    sample = StorageManager.simulate_expired_project(days_ago=days_ago)
    return {
        "status": "success",
        "message": f"已模拟注入一个 {days_ago} 天前的老项目，一键替换功能已自动淘汰！",
        "project": sample
    }

# ------------------ 角色库端点 ------------------
@router.get("/characters")
def list_characters():
    """
    获取反差角色基因库
    """
    chars = StorageManager.get_characters()
    return {"status": "success", "characters": chars}

@router.post("/characters")
def create_custom_character(req: CustomCharacterRequest):
    """
    保存用户自定义上传的替换角色
    """
    new_char = StorageManager.add_character({
        "name": req.name,
        "tag": req.tag or "自定义",
        "universe": "自定义用户角色",
        "prompt": req.prompt or f"反差开原风：把主角置换为【{req.name}】，神态霸气跳卡点舞",
        "avatar_url": req.avatar_url or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=200&auto=format&fit=crop",
        "badge": "用户上传"
    })
    return {"status": "success", "character": new_char}

# ------------------ 个人算力与交易端点 ------------------
@router.get("/user/profile")
def get_user_profile():
    profile = StorageManager.get_user_profile()
    return {"status": "success", "user": profile}

@router.post("/user/recharge")
def recharge_credits(req: RechargeRequest):
    new_credits = StorageManager.update_credits(req.credits)
    return {
        "status": "success",
        "recharged_credits": req.credits,
        "total_credits": new_credits,
        "package_name": req.package_name,
        "message": f"充值成功！已到账 +{req.credits} 算力"
    }

# ------------------ 合规申诉与 API 申请端点 ------------------
@router.post("/takedown")
def submit_takedown(req: TakedownRequest):
    takedowns = StorageManager.get_takedowns()
    ticket_id = f"TK-2026-{len(takedowns) + 1:03d}"
    record = {
        "id": ticket_id,
        "reason": "肖像权/版权申诉下架申请",
        "target_url": req.video_url,
        "description": req.description,
        "contact": req.contact,
        "submitted_at": "刚刚",
        "status": "pending"
    }
    takedowns.insert(0, record)
    StorageManager.save_takedowns(takedowns)
    return {
        "status": "success",
        "ticket_id": ticket_id,
        "message": "侵权申诉已受理！根据避风港原则，我们承诺在 2 小时内核查处置"
    }

@router.post("/api-apply")
def submit_api_apply(req: ApiApplyRequest):
    return {
        "status": "success",
        "message": f"开发者测试 Key 申请已受理！测试权限密钥将发送至 {req.email}"
    }

# ------------------ 即梦 & UpDream 无限画布与 GitHub 工作流端点 ------------------
class CanvasStateRequest(BaseModel):
    pan: Optional[Dict[str, Any]] = None
    zoom: Optional[float] = 0.9
    nodes: Optional[List[Dict[str, Any]]] = None
    links: Optional[List[Dict[str, Any]]] = None
    canvas_mode: Optional[str] = "infinite"

class ForkBranchRequest(BaseModel):
    character_name: str = "赵本山"
    engine: str = "MiniMax 海螺 H3"
    prompt: Optional[str] = ""

@router.get("/workflows/github")
def get_github_workflows():
    """
    学习 GitHub 开源 AI 视频与二创生态的精选工作流预设
    """
    workflows = StorageManager.get_github_workflows()
    return {
        "status": "success",
        "count": len(workflows),
        "workflows": workflows,
        "hint": "可直接点击将 GitHub 开源工作流载入即梦/UpDream 无限画布"
    }

@router.get("/canvas/state")
def get_canvas_state():
    """
    获取无限画布的节点与拓扑连线状态
    """
    state = StorageManager.get_canvas_state()
    return {"status": "success", "state": state}

@router.post("/canvas/save")
def save_canvas_state(req: CanvasStateRequest):
    """
    持久化保存创作者的无限画布创作拓扑
    """
    current = StorageManager.get_canvas_state()
    if req.pan: current["pan"] = req.pan
    if req.zoom is not None: current["zoom"] = req.zoom
    if req.nodes is not None: current["nodes"] = req.nodes
    if req.links is not None: current["links"] = req.links
    if req.canvas_mode: current["canvas_mode"] = req.canvas_mode
    StorageManager.save_canvas_state(current)
    return {"status": "success", "message": "无限画布状态已成功持久化"}

@router.post("/canvas/fork-branch")
def fork_canvas_branch(req: ForkBranchRequest):
    """
    UpDream 核心特性：从已有视频源派生新分支进行对照探索（不覆盖历史节点）
    """
    state = StorageManager.get_canvas_state()
    branch_id = f"node-branch-{uuid.uuid4().hex[:6]}"
    delivery_id = f"node-deliv-{uuid.uuid4().hex[:6]}"
    
    # 查找最大的 y 坐标进行平铺
    max_y = max([n.get("y", 100) for n in state.get("nodes", [])] + [100])
    new_y = max_y + 260
    
    char_node = {
        "id": branch_id,
        "type": "character",
        "title": f"🎭 派生分支: {req.character_name}",
        "x": 440,
        "y": new_y,
        "width": 310,
        "data": {
            "character": req.character_name,
            "nickname": "UpDream 并列分支",
            "avatar_badge": req.character_name[:2],
            "style_tag": req.engine,
            "fidelity": "99.0% 骨骼对齐"
        }
    }
    
    output_node = {
        "id": delivery_id,
        "type": "output_delivery",
        "title": f"🎬 分支成片: {req.character_name} · 探索直出",
        "x": 1560,
        "y": new_y - 60,
        "width": 360,
        "data": {
            "title": f"《{req.character_name}·分支对照实验成片》",
            "qc_score": 9.7,
            "status": "已就绪 / 对照中",
            "preview_url": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=600&auto=format&fit=crop"
        }
    }
    
    state["nodes"].append(char_node)
    state["nodes"].append(output_node)
    state["links"].append({"from": "node-scene-detect", "to": branch_id, "label": "分流切片"})
    state["links"].append({"from": branch_id, "to": output_node, "label": f"{req.engine} 并行渲染"})
    
    StorageManager.save_canvas_state(state)
    return {
        "status": "success",
        "message": f"已成功为【{req.character_name}】派生并列探索分支！保留原分支，画布实时双路渲染",
        "branch_node_id": branch_id,
        "output_node_id": delivery_id,
        "state": state
    }
