import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

# 项目根目录自动定位 (自适应跨平台，杜绝写死盘符)
# backend/app/core/config.py -> core -> app -> backend -> project_root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "MemeMorph Studio Backend API"
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # 持久化存储目录 (自动挂载至项目 storage 目录，亦支持环境变量重定向到对象存储或独立磁盘)
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", str(BASE_DIR / "storage"))
    
    # 本地工业级 Hypit 引擎路径 (自适应探测或环境变量指定)
    HYPIT_HOME: Optional[str] = os.getenv(
        "HYPIT_HOME",
        "D:/AI/gongzuoliu/clone video" if os.path.exists("D:/AI/gongzuoliu/clone video") else None
    )
    
    # 云端视频生成大模型接入配置 (可选，未配置时自动进入高保真智能 Mock / 演示模式)
    # 1. 字节跳动 Seedance (SEED 2.5 / 火山引擎方舟)
    VOLCENGINE_ACCESS_KEY: Optional[str] = None
    VOLCENGINE_SECRET_KEY: Optional[str] = None
    VOLCENGINE_ENDPOINT: str = "https://ark.cn-beijing.volces.com/api/v3"
    VOLCENGINE_MODEL_ENDPOINT_ID: Optional[str] = None  # 火山方舟在线推理接入点
    
    # 2. 快手可灵 Kling AI (Kling 1.5 电影版)
    KLING_API_KEY: Optional[str] = None
    KLING_ENDPOINT: str = "https://api.klingai.com/v1"
    
    # 3. MiniMax 海螺视频 (Video-01)
    MINIMAX_API_KEY: Optional[str] = None
    MINIMAX_GROUP_ID: Optional[str] = None
    MINIMAX_ENDPOINT: str = "https://api.minimax.chat/v1"
    
    # 4. VLM 视觉多模态质检与 Agent 裁决模型 (GPT-4o-mini / Gemini / Qwen-VL)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = "https://api.openai.com/v1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
