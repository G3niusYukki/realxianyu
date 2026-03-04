@echo off
chcp 65001 >nul
title 停止模块
color 0C

:: ========================================
:: 停止模块脚本
:: ========================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\.."

set "MODULE=%~1"

if "%MODULE%"=="" (
    echo [!] 错误: 未指定模块
    echo 用法: %~nx0 [presales^|operations^|aftersales^|all]
    exit /b 1
)

echo.
echo ===========================================
echo    停止模块: %MODULE%
echo ===========================================
echo.

:: 检查虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo [!] 未检测到虚拟环境
    exit /b 1
)

if "%MODULE%"=="all" (
    echo [*] 停止所有模块...
    call :STOP_MODULE presales
    call :STOP_MODULE operations
    call :STOP_MODULE aftersales
    echo.
    echo [✓] 所有模块已停止
) else (
    call :STOP_MODULE %MODULE%
)

pause
exit /b 0

:STOP_MODULE
set "TARGET=%~1"
set "STATE_FILE=data\module_runtime\%TARGET%.json"

if not exist "%STATE_FILE%" (
    echo [i] %TARGET%: 未运行
    goto :EOF
)

echo [*] 正在停止 %TARGET%...

:: 读取PID
for /f "tokens=*" %%a in ('.venv\Scripts\python -c "import json; print(json.load(open('%STATE_FILE%'))['pid'])" 2^>nul') do set "PID=%%a"

if "!PID!"=="" (
    echo [i] %TARGET%: 无法读取PID，清理状态文件
    del /f "%STATE_FILE%" 2>nul
    goto :EOF
)

echo     PID: !PID!

:: 尝试优雅停止
.venv\Scripts\python -c "
import os, signal, time, json, sys
from pathlib import Path

pid = int('!PID!')
state_file = Path('%STATE_FILE%')

try:
    # 发送SIGTERM
    os.kill(pid, signal.SIGTERM)
    print(f'  发送停止信号...')
    
    # 等待最多6秒
    for i in range(6):
        time.sleep(1)
        try:
            os.kill(pid, 0)  # 检查进程是否存在
        except OSError:
            print(f'  [✓] 进程已停止')
            # 删除状态文件
            if state_file.exists():
                state_file.unlink()
            sys.exit(0)
    
    # 强制终止
    print(f'  强制终止...')
    os.kill(pid, signal.SIGKILL)
    time.sleep(0.5)
    
    if state_file.exists():
        state_file.unlink()
    print(f'  [✓] 已强制停止')
    
except ProcessLookupError:
    print(f'  [i] 进程不存在')
    if state_file.exists():
        state_file.unlink()
except Exception as e:
    print(f'  [!] 错误: {e}')
    sys.exit(1)
"

if errorlevel 1 (
    echo [!] %TARGET%: 停止失败
) else (
    echo [✓] %TARGET%: 已停止
)

goto :EOF
