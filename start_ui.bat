@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONPATH=%~dp0backend

echo ========================================================
echo       MemeMorph Studio - FullStack Launcher
echo ========================================================
echo.

echo [1/3] Starting MemeMorph FastAPI Backend on port 8008...
start "MemeMorph-Backend" cmd /k "cd /d "%~dp0backend" && set PYTHONPATH=%~dp0backend && set PYTHONUTF8=1 && python -m uvicorn app.main:app --host 127.0.0.1 --port 8008 --reload"

timeout /t 2 /nobreak >nul

echo [2/3] Opening C-End User Workbench (prototype.html)...
start "" "prototype.html"

echo [3/3] Backend & Front-End successfully connected!
echo       Backend Port:  8008
echo       API Docs:      http://127.0.0.1:8008/docs
echo       Admin Console: admin.html (Account: Admin / Password: 123456)
echo.
echo ========================================================
echo Enter [A] and press Enter to open B-End Admin Console.
echo Or press Enter directly to finish launch.
echo ========================================================
set /p "CHOICE=Select [A / Enter]: "
if /i "%CHOICE%"=="A" (
    start "" "admin.html"
)
exit /b 0
