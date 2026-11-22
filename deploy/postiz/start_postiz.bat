@echo off
chcp 65001 >nul
echo ========================================================
echo       Postiz - 开源全平台社交媒体自动发布中枢
echo ========================================================
echo 正在检查 Docker 守护进程...

docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [提示] 检测到 Docker 守护进程未启动，正在尝试拉起 Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo 正在等待 Docker 服务初始化完成 (约需 15-20 秒)...
    timeout /t 18 /nobreak >nul
)

echo 正在启动 Postiz 多容器服务集群 (Postiz + PostgreSQL + Redis)...
cd /d "%~dp0"
docker compose up -d

echo --------------------------------------------------------
echo 服务已在后台启动！
echo 本地 Web 管理界面: http://localhost:5000
echo 默认账户: 首次访问直接注册管理员账户即可
echo --------------------------------------------------------
pause
