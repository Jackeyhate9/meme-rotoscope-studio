@echo off
chcp 65001 >nul
echo ========================================================
echo       MemeMorph 梗影AI - Model Context Protocol (MCP)
echo ========================================================
echo 正在以 stdio 协议启动 MemeMorph MCP 服务...
echo 适用客户端: Claude Desktop, OpenAI Codex, Cursor, Antigravity
echo 退出服务请按 Ctrl+C
echo --------------------------------------------------------

cd /d "%~dp0"
python run_mcp.py
