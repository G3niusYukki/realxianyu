@echo off
chcp 65001 >nul
title 闲鱼自动化 - 主菜单
color 0A

:: ========================================
:: 主控菜单 - 统一管理所有功能
:: ========================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\.."

:MENU
cls
echo.
echo ===========================================
echo    闲鱼自动化 - 主菜单
echo ===========================================
echo.
echo  [1] 启动模块
echo      └─ 售前模块 (自动回复/报价)
echo      └─ 运营模块 (擦亮/改价)
echo      └─ 售后模块 (发货/退款)
echo.
echo  [2] 查看状态
echo      └─ 查看各模块运行状态
echo.
echo  [3] 停止模块
echo      └─ 停止指定模块或全部
echo.
echo  [4] 系统工具
echo      └─ 健康检查
echo      └─ 查看日志
echo      └─ 系统诊断
echo.
echo  [5] 配置管理
echo      └─ 修改配置
echo      └─ 导入Cookie
echo.
echo  [6] Dashboard (网页管理)
echo.
echo  [0] 退出
echo.
echo ===========================================
set /p choice="请输入选项 (0-6): "

if "%choice%"=="1" goto :START_MODULE
if "%choice%"=="2" goto :CHECK_STATUS
if "%choice%"=="3" goto :STOP_MODULE
if "%choice%"=="4" goto :TOOLS
if "%choice%"=="5" goto :CONFIG
if "%choice%"=="6" goto :DASHBOARD
if "%choice%"=="0" exit /b 0
goto :MENU

:START_MODULE
cls
echo.
echo ===========================================
echo    启动模块
echo ===========================================
echo.
echo  [1] 售前模块 (自动回复 + 自动报价)
echo      └─ 使用Lite模式，无需浏览器
echo      └─ 通过WebSocket直连闲鱼
echo.
echo  [2] 运营模块 (擦亮/改价/上下架)
echo      └─ 需要配置闲鱼Cookie
echo.
echo  [3] 售后模块 (发货/退款处理)
echo      └─ 需要配置闲鱼Cookie
echo.
echo  [4] 启动全部模块
echo.
echo  [0] 返回主菜单
echo.
set /p mchoice="请输入选项 (0-4): "

if "%mchoice%"=="1" call "%SCRIPT_DIR%start_module.bat" presales
if "%mchoice%"=="2" call "%SCRIPT_DIR%start_module.bat" operations
if "%mchoice%"=="3" call "%SCRIPT_DIR%start_module.bat" aftersales
if "%mchoice%"=="4" (
    call "%SCRIPT_DIR%start_module.bat" presales
    call "%SCRIPT_DIR%start_module.bat" operations
    call "%SCRIPT_DIR%start_module.bat" aftersales
)
if "%mchoice%"=="0" goto :MENU
pause
goto :MENU

:CHECK_STATUS
call "%SCRIPT_DIR%status.bat"
pause
goto :MENU

:STOP_MODULE
cls
echo.
echo ===========================================
echo    停止模块
echo ===========================================
echo.
echo  [1] 停止售前模块
echo  [2] 停止运营模块
echo  [3] 停止售后模块
echo  [4] 停止所有模块
echo  [0] 返回主菜单
echo.
set /p schoice="请输入选项 (0-4): "

if "%schoice%"=="1" call "%SCRIPT_DIR%stop_module.bat" presales
if "%schoice%"=="2" call "%SCRIPT_DIR%stop_module.bat" operations
if "%schoice%"=="3" call "%SCRIPT_DIR%stop_module.bat" aftersales
if "%schoice%"=="4" call "%SCRIPT_DIR%stop_module.bat" all
if "%schoice%"=="0" goto :MENU
pause
goto :MENU

:TOOLS
cls
echo.
echo ===========================================
echo    系统工具
echo ===========================================
echo.
echo  [1] 健康检查 (doctor)
echo  [2] 查看日志
echo  [3] 系统诊断
echo  [4] 清理临时文件
echo  [0] 返回主菜单
echo.
set /p tchoice="请输入选项 (0-4): "

if "%tchoice%"=="1" (
    .venv\Scripts\python -m src.cli doctor --strict
    pause
)
if "%tchoice%"=="2" call "%SCRIPT_DIR%view_logs.bat"
if "%tchoice%"=="3" (
    .venv\Scripts\python -m src.cli module --action check --target all
    pause
)
if "%tchoice%"=="4" (
    echo [*] 清理临时文件...
    del /q /s *.pyc 2>nul
    rmdir /q /s __pycache__ 2>nul
    echo [✓] 清理完成
    pause
)
if "%tchoice%"=="0" goto :MENU
goto :MENU

:CONFIG
cls
echo.
echo ===========================================
echo    配置管理
echo ===========================================
echo.
echo  [1] 重新运行配置向导
echo  [2] 编辑配置文件 (.env)
echo  [3] 导入/更新Cookie
echo  [4] 配置闲管家API (可选)
echo  [0] 返回主菜单
echo.
set /p cchoice="请输入选项 (0-4): "

if "%cchoice%"=="1" call "%SCRIPT_DIR%simple_config.bat"
if "%cchoice%"=="2" (
    if exist .env (
        notepad .env
    ) else (
        echo [!] 配置文件不存在
        pause
    )
)
if "%cchoice%"=="3" (
    echo.
    echo 请使用Dashboard导入Cookie:
    echo   http://localhost:8091
echo.
    echo 或手动编辑 .env 文件
echo.
    pause
)
if "%cchoice%"=="4" (
    echo.
    echo 闲管家API配置:
    echo   1. 访问 https://open.taobao.com/
echo   2. 创建应用获取AppKey和AppSecret
echo   3. 在Dashboard中配置
echo.
    pause
)
if "%cchoice%"=="0" goto :MENU
goto :MENU

:DASHBOARD
echo.
echo [*] 启动Dashboard...
echo    访问地址: http://localhost:8091
echo.
start "" http://localhost:8091
.venv\Scripts\python -m src.dashboard_server --port 8091
goto :MENU
