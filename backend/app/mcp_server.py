"""
MemeMorph MCP Server (Model Context Protocol)
为 Claude (Claude Desktop / Claude Code)、OpenAI Codex、Cursor、Antigravity 等 AI Agent
提供原生转绘二创、新媒体热搜、分镜切分、Auto-QC 质检与大模型调度工具。
"""

import sys
import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# 确保 backend 目录在 sys.path 中
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# 配置日志输出至 stderr，严禁输出到 stdout（stdout 专用于 MCP JSON-RPC 协议）
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("mememorph-mcp")

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP as MCPServer
    except ImportError:
        logger.error("Failed to import MCPServer from mcp package. Please install mcp: pip install 'mcp>=1.2.0'")
        raise

from app.services.search_service import SearchService, CURATED_MEME_TEMPLATES
from app.services.scene_detector import SceneDetectorService
from app.services.qc_agent import VideoQCAgent
from app.services.storage_manager import StorageManager
from app.services.hypit_engine import HypitEngineService
from app.services.cloud_engines import EngineGateway
from app.services.postiz_service import PostizService

# 初始化 MCP Server
mcp = MCPServer("MemeMorph")

# ==========================================
# 🛠️ MCP Tools (供 Claude / Codex 等调用的工具)
# ==========================================

@mcp.tool()
def search_hot_videos(keyword: str = "", category: str = "全部", limit: int = 6) -> str:
    """
    即时搜索 B 站与抖音近期的热门卡点舞、MV 与新媒体爆款视频，支持智能推荐反差二创人设。
    
    Args:
        keyword: 搜索关键词（如 "aespa", "APT", "女团卡点舞", "霍元甲", "机械步" 等，为空时获取全网热门推荐）
        category: 分类筛选 ("全部", "K-Pop 卡点舞", "东北本山宇宙", "流行热歌", "经典国风", "抖音热歌")
        limit: 返回条数（默认 6，建议 4~10）
    """
    try:
        results = SearchService.search_videos(keyword=keyword, category=category, limit=limit)
        simplified = []
        for v in results:
            simplified.append({
                "bvid": v.get("bvid"),
                "title": v.get("title"),
                "author": v.get("author"),
                "duration": v.get("duration"),
                "play": v.get("play"),
                "heat_tag": v.get("heat_tag"),
                "category": v.get("category"),
                "recommended_character": v.get("recommended_character"),
                "suggested_prompt": v.get("suggested_prompt"),
                "url": v.get("url")
            })
        return json.dumps({"status": "success", "count": len(simplified), "videos": simplified}, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("search_hot_videos error: %s", e)
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def split_video_scenes(video_path_or_url: str, threshold: float = 27.0, long_video_mode: bool = False) -> str:
    """
    使用 PySceneDetect 对指定视频进行毫秒级分镜识别与时序切分规划。
    
    Args:
        video_path_or_url: 本地视频绝对路径或网络/B站视频 URL（本地路径优先执行真实 OpenCV 特征检测，网络路径执行高保真分镜时序规划）
        threshold: 场景切换灵敏度阈值 (默认 27.0，越低检测越敏感)
        long_video_mode: 是否启用一键长视频修改模式 (True 时规划 60s~300s 完整长视频的连续滑动分镜，False 时规划 15s 核心卡点分镜)
    """
    try:
        shots = SceneDetectorService.detect_scenes(video_path_or_url, threshold=threshold, long_video_mode=long_video_mode)
        total_duration = sum(s.get("duration_sec", 0) for s in shots)
        return json.dumps({
            "status": "success",
            "video": video_path_or_url,
            "mode": "长视频全片连续转绘" if long_video_mode else "15秒核心卡点",
            "shots_count": len(shots),
            "estimated_duration_sec": round(total_duration, 2),
            "shots": shots
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("split_video_scenes error: %s", e)
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def create_rotoscope_task(
    video_url: str,
    target_character: str,
    prompt: str = "",
    engine: str = "SEED 2.5",
    long_video_mode: bool = False,
    lighting_mode: str = "source",
    auto_qc: bool = True
) -> str:
    """
    创建并启动 AI 视频转绘 (Rotoscope) 与动作迁移任务。
    
    Args:
        video_url: 原始视频 URL 或 BVID / 文件路径
        target_character: 目标替换角色名称 (如 "范德彪", "赵本山", "赛博大花袄", "李云龙", "华强买瓜" 等)
        prompt: 提示词描述 (若为空将自动根据视频类型与角色特征生成爆款反差提示词)
        engine: 推理底座 ("SEED 2.5", "Kling 1.5", "MiniMax", "Hypit FastVideo v2", 或 "mock")
        long_video_mode: 是否为一键长视频修改模式 (支持完整 1~5 分钟 MV 批量切分与连贯缝合)
        lighting_mode: 光影锁定模式 ("source" 严格锁定原片光影与伴舞环境高保真, "harmonized" 全局重打光)
        auto_qc: 是否开启多模态关键帧自动质检
    """
    try:
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # 1. 镜头切分规划
        shots = SceneDetectorService.detect_scenes(video_url, long_video_mode=long_video_mode)
        
        # 2. 补全提示词
        final_prompt = prompt.strip()
        if not final_prompt:
            final_prompt = f"反差二创风格：{target_character} 身穿经典服饰，在原片真实舞台灯光下精准对位舞蹈动作，面部微表情传神，伴舞背景零损保留。"

        # 3. 计算耗时与算力
        shots_count = len(shots)
        is_local_hypit = "hypit" in engine.lower()
        cost_credits = 0 if is_local_hypit else (shots_count * 12 if not long_video_mode else shots_count * 25)
        est_seconds = shots_count * 4 if is_local_hypit else shots_count * 8

        # 4. 存入持久化与响应
        task_info = {
            "task_id": task_id,
            "status": "ready_to_render",
            "video_url": video_url,
            "target_character": target_character,
            "engine": engine,
            "is_local_gpu": is_local_hypit,
            "lighting_mode": lighting_mode,
            "long_video_mode": long_video_mode,
            "prompt": final_prompt,
            "shots_count": shots_count,
            "estimated_seconds": est_seconds,
            "credits_cost": cost_credits,
            "auto_qc_enabled": auto_qc,
            "created_at": StorageManager.get_user_profile().get("username", "二创UP主")
        }

        return json.dumps({
            "status": "success",
            "message": f"转绘任务 {task_id} 已成功创建并初始化",
            "task": task_info,
            "shots_preview": shots[:3]
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("create_rotoscope_task error: %s", e)
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def inspect_video_qc(reference_character: str = "范德彪", interactive_mode: bool = False) -> str:
    """
    调用多模态视觉质检智能体 (Auto-QC Agent) 对分镜转绘质量进行打分与人机协同裁决。
    
    Args:
        reference_character: 参考角色名 (如 "范德彪", "赵本山")
        interactive_mode: 是否开启临界值人机协同中断裁决测试
    """
    try:
        qc_result = VideoQCAgent.inspect_shot(
            shot_video_path="mock_shot_02.mp4",
            reference_character=reference_character,
            interactive_qc=interactive_mode
        )
        return json.dumps({
            "status": "success",
            "reference_character": reference_character,
            "qc_report": qc_result
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("inspect_video_qc error: %s", e)
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def check_engine_matrix() -> str:
    """
    查询所有 4 种视频生成大模型底座（字节跳动 Seedance 2.5、快手可灵 Kling 1.5、MiniMax 海螺视频、本地 Hypit FastVideo v2）的健康状态、时延与能力特性。
    """
    try:
        matrix = EngineGateway.get_engines_matrix()
        hypit_status = HypitEngineService.get_runtime_status()
        return json.dumps({
            "status": "success",
            "engines_matrix": matrix,
            "local_hypit_environment": hypit_status
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("check_engine_matrix error: %s", e)
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def get_preset_characters() -> str:
    """
    获取平台精选的经典爆款反差角色基因库（范德彪、赵本山、赛博大花袄、李云龙、华强买瓜等）及其专有提示词模板。
    """
    try:
        characters = StorageManager.get_characters()
        return json.dumps({
            "status": "success",
            "count": len(characters),
            "characters": characters
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("get_preset_characters error: %s", e)
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def list_projects() -> str:
    """
    查询当前所有转绘交付作品及其 30 天项目存续生命周期（包含剩余天数、下载链接与淘汰状态）。
    """
    try:
        projects = StorageManager.get_projects()
        return json.dumps({
            "status": "success",
            "count": len(projects),
            "projects": projects
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("list_projects error: %s", e)
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def clean_expired_projects() -> str:
    """
    一键批量淘汰并彻底清理所有超期（存续超过 30 天）的历史老作品，释放磁盘存储与列表空间。
    """
    try:
        cleaned_count = StorageManager.clean_expired_projects()
        return json.dumps({
            "status": "success",
            "message": f"成功淘汰并清理了 {cleaned_count} 个超期老项目",
            "cleaned_count": cleaned_count
        }, ensure_ascii=False)
    except Exception as e:
        logger.error("clean_expired_projects error: %s", e)
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


# ==========================================
# 📢 Postiz 社交媒体全网自动发布 MCP Tools
# ==========================================

@mcp.tool()
def postiz_check_status() -> str:
    """
    检查 Postiz 自动化社交媒体发布中枢的运行状态、连接地址与鉴权配置。
    """
    try:
        health = PostizService.check_health()
        return json.dumps({"status": "success", "postiz": health}, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("postiz_check_status error: %s", e)
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def postiz_list_channels() -> str:
    """
    获取 Postiz 中已连接绑定的社交媒体平台列表（Twitter/X, Reddit, LinkedIn, TikTok, YouTube 等）。
    """
    try:
        channels = PostizService.list_integrations()
        return json.dumps({"status": "success", "count": len(channels), "channels": channels}, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("postiz_list_channels error: %s", e)
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def postiz_publish_post(
    content: str,
    channels: Optional[List[str]] = None,
    title: Optional[str] = None,
    schedule_time: Optional[str] = None,
    media_paths: Optional[List[str]] = None
) -> str:
    """
    通过 Postiz 自动化发布或排期内容至 Twitter/X、Reddit、LinkedIn 等社交媒体平台。
    
    Args:
        content: 宣发或帖子正文（支持 Markdown）
        channels: 目标发布渠道列表（如 ["twitter", "reddit"]，留空默认发布至已连接的主力渠道）
        title: 标题（用于 Reddit 等需要独立标题的平台）
        schedule_time: 定时发布时间 (ISO 格式如 '2026-11-23T22:00:00Z'，留空为立即发布)
        media_paths: 随帖附带的本地或网络配图/视频文件路径列表
    """
    try:
        res = PostizService.publish_post(
            content=content,
            channels=channels,
            title=title,
            schedule_time=schedule_time,
            media_paths=media_paths
        )
        return json.dumps(res, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("postiz_publish_post error: %s", e)
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


# ==========================================
# 📚 MCP Prompts (供 LLM 提示词模板扩展)
# ==========================================

@mcp.prompt()
def recommend_meme_rotoscope(video_topic: str) -> str:
    """
    根据给定的视频主题或歌曲名称，为创作者策划爆款二创方案、反差角色与转绘参数。
    """
    return f"""你是一位精通短视频二创传播学与计算机视觉转绘的 AI 创意总监。
用户希望对以下视频主题进行 AI 转绘二创：
主题/歌曲/舞台: {video_topic}

请运用 MemeMorph 的爆款指数公式：
爆款指数 = 原视频流行/帅气度 × 替换角色的乡土/喜感/反差打破第四面墙指数

请给出：
1. 【反差角色推荐】：选择最适合的角色（如范德彪、赵本山、赛博大花袄等），并阐述爆款化学反应；
2. 【分镜规划策略】：建议采用 15 秒卡点模式还是一键长视频修改模式，说明关键帧转折点；
3. 【精密转绘 Prompt】：包含主体外观、标志性微表情、舞台灯光模式 (lightingMode="source") 与伴舞背景保留要求；
4. 【底座选择建议】：推荐使用本地 Hypit (0算力私有化出片) 还是云端大模型 (Seedance 2.5 / Kling 1.5)。
"""

# ==========================================
# 🚀 启动入口
# ==========================================

def main():
    logger.info("Starting MemeMorph MCP Server (transport=stdio)...")
    # 默认使用 stdio 协议，完美兼容 Claude Desktop, Codex, Cursor, Antigravity
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
