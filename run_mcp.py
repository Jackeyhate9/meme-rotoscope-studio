"""
MemeMorph MCP Server Runner
使用 stdio 协议启动 MemeMorph MCP 服务，直接接入 Claude Desktop、OpenAI Codex、Cursor 等客户端。
"""

import sys
from pathlib import Path

# 添加 backend 到搜索路径
project_root = Path(__file__).resolve().parent
backend_dir = project_root / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.mcp_server import main

if __name__ == "__main__":
    main()
