@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo       MemeMorph Ops Console - Admin Launcher
echo ========================================================
echo.
echo Opening B-End Admin Console in default browser...
echo File:           admin.html
echo Default User:   Admin
echo Default Pass:   123456
echo.
start "" "admin.html"
exit /b 0
