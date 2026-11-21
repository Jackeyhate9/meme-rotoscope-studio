import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)
STORAGE_DIR = settings.STORAGE_DIR

class StorageManager:
    """
    负责本地持久化与数据生命周期管理，包含：
    1. 用户作品/项目持久化
    2. 30天（1个月）项目有效期与一键替换功能淘汰判定
    3. 过期老项目一键批量清理淘汰，防止界面与存储堆积
    4. 角色库、审核池、算力账户与工单持久化
    """

    @classmethod
    def _get_path(cls, filename: str) -> str:
        os.makedirs(STORAGE_DIR, exist_ok=True)
        return os.path.join(STORAGE_DIR, filename)

    @classmethod
    def _load_json(cls, filename: str, default: Any) -> Any:
        path = cls._get_path(filename)
        if not os.path.exists(path):
            cls._save_json(filename, default)
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    @classmethod
    def _save_json(cls, filename: str, data: Any):
        path = cls._get_path(filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ------------------ 用户信息与算力 ------------------
    @classmethod
    def get_user_profile(cls) -> Dict[str, Any]:
        default_user = {
            "username": "二创UP主",
            "credits": 120,
            "tier": "创作者会员",
            "avatar_text": "UP",
            "total_generated": 14,
            "vip_valid_until": "2026-12-31"
        }
        return cls._load_json("user_profile.json", default_user)

    @classmethod
    def update_credits(cls, delta: int) -> int:
        user = cls.get_user_profile()
        user["credits"] = max(0, user.get("credits", 0) + delta)
        cls._save_json("user_profile.json", user)
        return user["credits"]

    # ------------------ 角色库管理 ------------------
    @classmethod
    def get_characters(cls) -> List[Dict[str, Any]]:
        default_chars = [
            {
                "id": "char_fdb",
                "name": "范德彪",
                "tag": "彪哥",
                "universe": "辽北第一狠人宇宙",
                "prompt": "反差开原风：范德彪身穿维多利亚经典西装，黑色大墨镜，霸气歪嘴神态跳 K-Pop 卡点女团舞，保留招牌鹰爪挠手势。",
                "avatar_url": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=200&auto=format&fit=crop",
                "calls_count": 12420,
                "is_active": True,
                "badge": "最热推荐"
            },
            {
                "id": "char_zbs",
                "name": "赵本山",
                "tag": "大叔",
                "universe": "白云黑土小品宇宙",
                "prompt": "复古开原风：身穿经典蓝色中山棉袄，头戴雷锋羊毛帽，质朴喜感表情，配合太空步与三道弯机械动作严格卡点。",
                "avatar_url": "https://images.unsplash.com/photo-1547153760-18fc86324498?q=80&w=200&auto=format&fit=crop",
                "calls_count": 8930,
                "is_active": True,
                "badge": "经典反差"
            },
            {
                "id": "char_lyl",
                "name": "李云龙",
                "tag": "老李",
                "universe": "亮剑正剧反差",
                "prompt": "亮剑反差风：粗布八路军军装，铁血硬汉气质与粗犷霸道目光，跳深情双人爵士舞，神情反差萌爆笑拉满。",
                "avatar_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=200&auto=format&fit=crop",
                "calls_count": 6120,
                "is_active": True,
                "badge": "鬼畜顶流"
            },
            {
                "id": "char_cbh",
                "name": "赛博大花袄",
                "tag": "大花",
                "universe": "国潮概念皮肤",
                "prompt": "赛博国潮风：东北大红大绿艳丽棉花袄高保真纹理，融入赛博朋克面部机械发光纹路，舞台伴随霓虹灯光效律动。",
                "avatar_url": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?q=80&w=200&auto=format&fit=crop",
                "calls_count": 4350,
                "is_active": True,
                "badge": "视觉冲击"
            }
        ]
        return cls._load_json("characters.json", default_chars)

    @classmethod
    def add_character(cls, char_data: Dict[str, Any]) -> Dict[str, Any]:
        chars = cls.get_characters()
        char_data["id"] = f"char_custom_{int(time.time())}"
        char_data["calls_count"] = 0
        char_data["is_active"] = True
        chars.insert(0, char_data)
        cls._save_json("characters.json", chars)
        return char_data

    # ------------------ 项目生命周期与一键替换淘汰 ------------------
    VALIDITY_DAYS = 30  # 一般为 1 个月有效期

    @classmethod
    def get_projects(cls) -> List[Dict[str, Any]]:
        """
        获取全部历史二创项目，并计算有效期状态：
        若创建时间超过 VALIDITY_DAYS（30天），则自动标记为已过期（is_expired = True），
        并将其“一键替换”功能淘汰（can_replace = False），防止界面无休止堆积。
        """
        default_projects = [
            {
                "id": "proj_current_demo",
                "title": "作品交付：《当范德彪误入 K-pop 练习生海选》 (15s 高清完整版)",
                "character": "范德彪",
                "prompt": "反差开原风：范德彪身穿维多利亚西装，神情霸气跳 K-Pop 卡点女团舞，保留经典鹰爪挠手势",
                "video_url": "https://www.bilibili.com/video/BV1xx411c7X_KpopDance",
                "cover_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=800&auto=format&fit=crop",
                "result_url": "https://assets.mememorph.ai/demo_result_1080p.mp4",
                "shots_count": 3,
                "duration_sec": 14.8,
                "credits_cost": 45,
                "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "status": "completed",
                "qc_score": 9.4,
                "shots": [
                    {
                        "shot_id": 1,
                        "title": "镜头 01 (近景面部)",
                        "time_range": "00:00 - 00:04",
                        "status": "质检通过 (9.4)",
                        "image_url": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=400&auto=format&fit=crop"
                    },
                    {
                        "shot_id": 2,
                        "title": "镜头 02 (全身连贯舞)",
                        "time_range": "00:04 - 00:09",
                        "status": "质检通过 (9.2)",
                        "image_url": "https://images.unsplash.com/photo-1547153760-18fc86324498?q=80&w=400&auto=format&fit=crop"
                    },
                    {
                        "shot_id": 3,
                        "title": "镜头 03 (舞台定格)",
                        "time_range": "00:09 - 00:15",
                        "status": "质检通过 (9.6)",
                        "image_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=400&auto=format&fit=crop"
                    }
                ]
            },
            {
                "id": "proj_expired_sample",
                "title": "作品交付：《赵本山太空步 × 机械锁舞solo》 (已过1个月淘汰归档)",
                "character": "赵本山",
                "prompt": "全员复古：身穿绿色雷锋棉袄、皮草雷锋帽，雪地舞台光效，背景出现二人转秧歌红绸",
                "video_url": "https://www.bilibili.com/video/BV1yy411d8Y_LockDance",
                "cover_url": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=800&auto=format&fit=crop",
                "result_url": "https://assets.mememorph.ai/demo_zbs_lock_1080p.mp4",
                "shots_count": 4,
                "duration_sec": 14.0,
                "credits_cost": 45,
                # 模拟 36 天前生成的历史老项目（已超 30 天淘汰期限）
                "created_at": (datetime.now() - timedelta(days=36)).isoformat(),
                "status": "completed",
                "qc_score": 9.2,
                "shots": [
                    {
                        "shot_id": 1,
                        "title": "镜头 01 (起手锁步)",
                        "time_range": "00:00 - 00:03",
                        "status": "已归档",
                        "image_url": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=400&auto=format&fit=crop"
                    }
                ]
            }
        ]

        raw_projects = cls._load_json("projects.json", default_projects)
        now = datetime.now()

        enriched_projects = []
        for p in raw_projects:
            created_dt = None
            try:
                created_dt = datetime.fromisoformat(p.get("created_at", ""))
            except Exception:
                created_dt = now - timedelta(days=1)

            age_days = (now - created_dt).total_seconds() / (24 * 3600)
            is_expired = age_days >= cls.VALIDITY_DAYS
            remaining_days = max(0, int(cls.VALIDITY_DAYS - age_days))

            p_copy = dict(p)
            p_copy["age_days"] = round(age_days, 1)
            p_copy["is_expired"] = is_expired
            p_copy["validity_days_total"] = cls.VALIDITY_DAYS
            p_copy["remaining_days"] = remaining_days
            # 核心业务契约：超过1个月有效期后，一键替换功能直接淘汰！
            p_copy["can_replace"] = not is_expired
            p_copy["sunset_reason"] = "已超过30天（1个月）有效期，底层动作特征与动捕临时切片已淘汰释放，不支持一键替换" if is_expired else "处于1个月保护期内，支持一键替换与再二创"

            enriched_projects.append(p_copy)

        return enriched_projects

    @classmethod
    def save_project(cls, project_data: Dict[str, Any]):
        projects = cls.get_projects()
        if "created_at" not in project_data:
            project_data["created_at"] = datetime.now().isoformat()
        # 移除计算字段后再存储
        clean_proj = {k: v for k, v in project_data.items() if k not in ["age_days", "is_expired", "remaining_days", "can_replace", "sunset_reason"]}
        projects.insert(0, clean_proj)
        cls._save_json("projects.json", projects)

    @classmethod
    def delete_project(cls, project_id: str) -> bool:
        projects = cls.get_projects()
        filtered = [p for p in projects if p.get("id") != project_id]
        if len(filtered) != len(projects):
            cls._save_json("projects.json", filtered)
            return True
        return False

    @classmethod
    def clean_expired_projects(cls) -> Dict[str, Any]:
        """
        一键清理淘汰所有已超过1个月有效期的老项目，
        防止前端作品列表和服务器存储越积越多！
        """
        projects = cls.get_projects()
        valid_projects = []
        cleaned_count = 0
        cleaned_titles = []

        for p in projects:
            if p.get("is_expired"):
                cleaned_count += 1
                cleaned_titles.append(p.get("title", p.get("id")))
            else:
                clean_p = {k: v for k, v in p.items() if k not in ["age_days", "is_expired", "remaining_days", "can_replace", "sunset_reason"]}
                valid_projects.append(clean_p)

        cls._save_json("projects.json", valid_projects)
        return {
            "cleaned_count": cleaned_count,
            "cleaned_titles": cleaned_titles,
            "remaining_count": len(valid_projects),
            "message": f"成功淘汰并清理 {cleaned_count} 个超期（>30天）老项目，释放前端列表空间！"
        }

    @classmethod
    def simulate_expired_project(cls, days_ago: int = 35) -> Dict[str, Any]:
        """
        测试辅助功能：注入或重置一个指定天数前创建的项目，方便前端直观测试有效期与淘汰功能
        """
        sample = {
            "id": f"proj_sim_{int(time.time())}",
            "title": f"作品交付：《模拟老项目·{days_ago}天前生成》 (测试淘汰效果)",
            "character": "赛博大花袄",
            "prompt": "国潮秧歌红花绿叶纹理与电子霓虹灯的魔幻融合",
            "video_url": "https://www.bilibili.com/video/BV1simulated_test",
            "cover_url": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?q=80&w=800&auto=format&fit=crop",
            "result_url": "https://assets.mememorph.ai/demo_result_1080p.mp4",
            "shots_count": 3,
            "duration_sec": 14.5,
            "credits_cost": 45,
            "created_at": (datetime.now() - timedelta(days=days_ago)).isoformat(),
            "status": "completed",
            "qc_score": 9.1,
            "shots": [
                {
                    "shot_id": 1,
                    "title": "镜头 01 (模拟分镜)",
                    "time_range": "00:00 - 00:05",
                    "status": "已归档淘汰",
                    "image_url": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?q=80&w=400&auto=format&fit=crop"
                }
            ]
        }
        cls.save_project(sample)
        return sample

    # ------------------ 审核队列与侵权工单 ------------------
    @classmethod
    def get_crawler_queue(cls) -> List[Dict[str, Any]]:
        default_queue = [
            {
                "id": "queue-item-1",
                "title": "《K-Pop 超能新歌 C位魔性击剑舞》",
                "source": "B站热搜 No.2",
                "duration": "15.2s",
                "bvid": "BV1xx411c7X",
                "url": "https://www.bilibili.com/video/BV1xx411c7X",
                "cover_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=400&auto=format&fit=crop",
                "idea_summary": "将女团 C 位换成【范德彪维多利亚西装】，双手套用鹰爪挠姿势卡点",
                "character": "范德彪",
                "vlm_score": 9.7,
                "shots_count": 3,
                "discovered_at": "28分钟前"
            },
            {
                "id": "queue-item-2",
                "title": "《西装暴徒机械步：节奏重低音卡点》",
                "source": "抖音爆款挑战",
                "duration": "14.0s",
                "bvid": "BV1yy411d8Y",
                "url": "https://www.bilibili.com/video/BV1yy411d8Y",
                "cover_url": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=400&auto=format&fit=crop",
                "idea_summary": "替换为【赵本山二人转白云黑土风】，雪地舞台灯光",
                "character": "赵本山",
                "vlm_score": 9.4,
                "shots_count": 4,
                "discovered_at": "1小时前"
            }
        ]
        return cls._load_json("crawler_queue.json", default_queue)

    @classmethod
    def save_crawler_queue(cls, queue: List[Dict[str, Any]]):
        cls._save_json("crawler_queue.json", queue)

    @classmethod
    def get_takedowns(cls) -> List[Dict[str, Any]]:
        default_takedowns = [
            {
                "id": "TK-2026-003",
                "reason": "肖像权侵权下架申请",
                "target_url": "https://mememorph.ai/video/BV1xx411c7X_demo",
                "complainant": "某经纪公司法务代表",
                "contact": "legal@entertainment.com",
                "submitted_at": "45分钟前",
                "status": "pending"
            }
        ]
        return cls._load_json("takedowns.json", default_takedowns)

    @classmethod
    def save_takedowns(cls, takedowns: List[Dict[str, Any]]):
        cls._save_json("takedowns.json", takedowns)

    # ------------------ GitHub 开源工作流库与无限画布持久化 ------------------
    @classmethod
    def get_github_workflows(cls) -> List[Dict[str, Any]]:
        """
        学习 GitHub 顶级 AI 视频开源项目提炼的爆款二创工作流预设
        """
        workflows = [
            {
                "id": "workflow-comfyui-rotoscope",
                "name": "ComfyUI-Meme-Rotoscope",
                "title": "ComfyUI 官方精选二创流水线",
                "repo": "comfyanonymous/ComfyUI",
                "repo_url": "https://github.com/comfyanonymous/ComfyUI",
                "stars": "56.8k",
                "license": "GPL-3.0",
                "author": "ComfyUI Community & MemeMorph",
                "badge": "官方推荐 · 爆款首选",
                "tech_stack": ["PySceneDetect", "Meta SAM 2", "ControlNet Pose", "SEED 2.5", "Auto-QC"],
                "description": "借鉴 GitHub 最流行的 ComfyUI 节点式视频转绘生态。将 15s 原视频切为 3 镜独立时序，通过 SAM 2 锁定 C 位主角，完美保留背景伴舞，注入反差角色脸谱与骨骼。",
                "recommended_character": "范德彪",
                "recommended_engine": "SEED 2.5",
                "default_prompt": "反差开原风：范德彪身穿维多利亚西装，神情霸气跳 K-Pop 卡点女团舞，保留经典鹰爪挠手势",
                "nodes_count": 6,
                "has_branch": False
            },
            {
                "id": "workflow-updream-dual-branch",
                "name": "UpDream-Dual-Branch-Explore",
                "title": "UpDream 风格双分支并列探索工作流",
                "repo": "bilibili/updream-canvas-workflows",
                "repo_url": "https://github.com/bilibili",
                "stars": "24.2k",
                "license": "Apache-2.0",
                "author": "B站 UP主开源创作联合会",
                "badge": "UpDream 精选 · 分支探索不覆盖",
                "tech_stack": ["UpDream Canvas", "Dual-Branch", "SEED 2.5", "MiniMax H3", "Side-by-Side QC"],
                "description": "完美复现 B站 updream 无限画布的核心精髓：保留每一个探索分支！同一视频源同时拉出【分支A: 范德彪女团打歌】与【分支B: 赵本山大雪秧歌】，并在画布并列呈现双路成片直出对比。",
                "recommended_character": "范德彪 / 赵本山 (双路)",
                "recommended_engine": "SEED 2.5 + MiniMax H3",
                "default_prompt": "分支A: 范德彪西装卡点；分支B: 赵本山大秧歌极乐净土",
                "nodes_count": 9,
                "has_branch": True
            },
            {
                "id": "workflow-liveportrait-kpop",
                "name": "LivePortrait-Idol-Meme",
                "title": "LivePortrait 偶像微表情神态迁移",
                "repo": "KwaiVGI/LivePortrait",
                "repo_url": "https://github.com/KwaiVGI/LivePortrait",
                "stars": "18.3k",
                "license": "MIT",
                "author": "KwaiVGI Team",
                "badge": "极速微表情 · 歪嘴卡点",
                "tech_stack": ["LivePortrait", "Wav2Lip-HQ", "Facial Dynamics", "SEED 2.5"],
                "description": "学习快手开源的 LivePortrait 深度微表情捕捉网络。针对 K-Pop 偶像眨眼、挑眉、歪嘴笑容实现 1:1 精确反差表情迁移，生成极具鬼畜笑果的特写分镜。",
                "recommended_character": "李云龙",
                "recommended_engine": "SEED 2.5",
                "default_prompt": "亮剑反差风：李云龙表情威严严肃，对口型唱跳魔性女团高音副歌，眼神霸气侧漏",
                "nodes_count": 6,
                "has_branch": False
            },
            {
                "id": "workflow-animatediff-dance",
                "name": "AnimateDiff-Dance-Motion",
                "title": "AnimateDiff 动态权重与背景灯光保真",
                "repo": "guoyww/AnimateDiff",
                "repo_url": "https://github.com/guoyww/AnimateDiff",
                "stars": "23.9k",
                "license": "Apache-2.0",
                "author": "AnimateDiff Research",
                "badge": "动作平滑 · 无闪烁",
                "tech_stack": ["AnimateDiff v3", "Motion LoRA", "Inpainting Mask", "Kling 1.5"],
                "description": "基于 GitHub AnimateDiff 视频运动生成框架，强化帧间一致性与光影流转，彻底解决多人物场景下的边缘重影与背景抽搐问题。",
                "recommended_character": "赛博红棉袄",
                "recommended_engine": "Kling 1.5",
                "default_prompt": "国潮赛博风：赛博大花袄女战士，在充满霓虹光晕的舞台中利落起舞，舞台激光特效绚烂",
                "nodes_count": 6,
                "has_branch": False
            },
            {
                "id": "workflow-minimax-acrobatics",
                "name": "MiniMax-H3-Acrobatics",
                "title": "MiniMax 极速街舞与大幅度肢体物理强化",
                "repo": "MiniMax-AI/Hailuo-Video-Tools",
                "repo_url": "https://github.com/MiniMax-AI",
                "stars": "12.5k",
                "license": "MIT",
                "author": "MiniMax Developer Group",
                "badge": "大幅度动作 · 街舞专属",
                "tech_stack": ["MiniMax H3", "Physical Inertia", "Auto-QC Re-roll", "Real-ESRGAN"],
                "description": "针对高难度街舞托马斯全旋、大跳与剧烈手势卡点设计的物理惯性增强工作流，大幅减少肢体拉伸断裂，保证动感画面丝滑连贯。",
                "recommended_character": "范德彪",
                "recommended_engine": "MiniMax 海螺 H3",
                "default_prompt": "动作极速爆发：范德彪化身街舞达人，手势鹰爪挠配合快速倒立旋转，地面震荡波与重低音共振",
                "nodes_count": 6,
                "has_branch": False
            },
            {
                "id": "workflow-hypit-fastvideo-flex",
                "name": "Hypit-Character-Swap-FastVideo",
                "title": "Hypit 本地工业级人物替换 (FastVideo v2 6步 · 零算力成本)",
                "repo": "hypit-local / local-models",
                "repo_url": "https://github.com/ag-ui-protocol/ag-ui",
                "stars": "本地就绪",
                "license": "Custom/Local",
                "author": "Hypit Local Engine Team",
                "badge": "⚡ 本地首选 · 零 API 成本",
                "tech_stack": ["Hypit Local", "FastVideo v2", "Pika Flex (6步)", "lightingMode=source", "swap-assemble", "AG-UI Stream"],
                "description": "接入本机已配置的 Hypit 本地工程底座。采用 FastVideo v2 (Pika Flex, 6步) 极速动作迁移，5秒分镜窗口严密对齐，开启 lightingMode=\"source\" 完美锁定原舞台射灯与溢光，CPU 无损拼接原声音频，免 API 采购费用。",
                "recommended_character": "赵本山",
                "recommended_engine": "Local Hypit (FastVideo v2)",
                "default_prompt": "开原大舞厅特别版：赵本山身穿标志性绿色雷锋棉袄、皮草雷锋帽，跟随女团快节奏跳太空步卡点反差爆笑舞",
                "nodes_count": 6,
                "has_branch": False
            }
        ]
        return workflows

    @classmethod
    def get_canvas_state(cls) -> Dict[str, Any]:
        """
        获取当前无限画布的节点与连线状态
        """
        default_state = {
            "version": "2.5.0",
            "canvas_mode": "infinite",
            "pan": {"x": 100, "y": 80},
            "zoom": 0.9,
            "nodes": [
                {
                    "id": "node-video-input",
                    "type": "video_input",
                    "title": "📹 原视频输入节点",
                    "x": 60,
                    "y": 80,
                    "width": 320,
                    "data": {
                        "video_url": "https://www.bilibili.com/video/BV1xx411c7X_KpopDance",
                        "title": "【4K60帧】2026 KGMA女团舞台高潮合集",
                        "duration": "14.8s",
                        "source": "B站热搜 No.1",
                        "cover_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=600&auto=format&fit=crop"
                    }
                },
                {
                    "id": "node-scene-detect",
                    "type": "scene_detect",
                    "title": "✂️ PySceneDetect 分镜时序",
                    "x": 440,
                    "y": 80,
                    "width": 310,
                    "data": {
                        "shots_count": 3,
                        "shots": [
                            {"name": "分镜 #01 (特写 0-4s)", "type": "面部歪嘴表情置换", "score": 9.4},
                            {"name": "分镜 #02 (全身 4-9s)", "type": "肢体鹰爪挠舞步保持", "score": 9.2},
                            {"name": "分镜 #03 (舞台 9-15s)", "type": "霓虹灯维多利亚舞台", "score": 9.6}
                        ]
                    }
                },
                {
                    "id": "node-char-branch-1",
                    "type": "character",
                    "title": "🎭 角色基因卡: 范德彪 (主线)",
                    "x": 440,
                    "y": 420,
                    "width": 310,
                    "data": {
                        "character": "范德彪",
                        "nickname": "辽北第一狠人",
                        "avatar_badge": "彪哥",
                        "style_tag": "维多利亚西装",
                        "fidelity": "98.4% 骨骼锁定"
                    }
                },
                {
                    "id": "node-prompt-brain",
                    "type": "prompt_brain",
                    "title": "💡 AI 创意大脑提示词",
                    "x": 820,
                    "y": 180,
                    "width": 320,
                    "data": {
                        "formula": "帅气女团原舞 × 彪哥乡土反差 = 泼天流量",
                        "prompt": "反差开原风：范德彪身穿维多利亚西装，神情霸气跳 K-Pop 卡点女团舞，保留经典鹰爪挠手势",
                        "agent_idea": "方案 A: 辽北第一狠人女团打歌"
                    }
                },
                {
                    "id": "node-engine-renderer",
                    "type": "engine_renderer",
                    "title": "⚙️ 引擎调度与 Auto-QC 质检",
                    "x": 1200,
                    "y": 140,
                    "width": 300,
                    "data": {
                        "engine": "SEED 2.5",
                        "auto_qc": True,
                        "cost": 45,
                        "status": "就绪",
                        "est_time": "14.2s"
                    }
                },
                {
                    "id": "node-output-delivery",
                    "type": "output_delivery",
                    "title": "🎬 成片交付与双视窗直出",
                    "x": 1560,
                    "y": 80,
                    "width": 360,
                    "data": {
                        "title": "《范德彪·维多利亚打歌卡点舞》",
                        "qc_score": 9.4,
                        "status": "已就绪 / 可一键替换",
                        "preview_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=600&auto=format&fit=crop"
                    }
                }
            ],
            "links": [
                {"from": "node-video-input", "to": "node-scene-detect", "label": "15s 视频流"},
                {"from": "node-scene-detect", "to": "node-prompt-brain", "label": "3段切点特征"},
                {"from": "node-char-branch-1", "to": "node-prompt-brain", "label": "角色面部基因"},
                {"from": "node-prompt-brain", "to": "node-engine-renderer", "label": "多模态 Prompt"},
                {"from": "node-engine-renderer", "to": "node-output-delivery", "label": "质检合格成片 (9.4)"}
            ]
        }
        return cls._load_json("canvas_state.json", default_state)

    @classmethod
    def save_canvas_state(cls, state: Dict[str, Any]):
        cls._save_json("canvas_state.json", state)
