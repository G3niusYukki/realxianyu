@echo off
chcp 65001 >nul
title 模块状态
color 0B

:: ========================================
:: 查看模块运行状态
:: ========================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\.."

echo.
echo ===========================================
echo    模块运行状态
echo ===========================================
echo.
echo 检查时间: %date% %time%
echo.

:: 检查虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo [!] 未检测到虚拟环境
    echo     请先运行 install.bat 进行部署
    pause
    exit /b 1
)

:: 检查各模块状态
call :CHECK_MODULE presales 售前模块
call :CHECK_MODULE operations 运营模块
call :CHECK_MODULE aftersales 售后模块

echo.
echo ===========================================
echo.

:: 使用Python检查并显示更详细的信息
.venv\Scripts\python -c "
import json
import os
from pathlib import Path
from datetime import datetime

runtime_dir = Path('data/module_runtime')
if not runtime_dir.exists():
    print('[i] 暂无运行中的模块')
    exit(0)

print('详细信息:')
print('-' * 50)

found_any = False
for state_file in runtime_dir.glob('*.json'):
    found_any = True
    module = state_file.stem
    try:
        state = json.load(open(state_file))
        pid = state.get('pid', '?')
        started = state.get('started_at', '未知')
        log_file = state.get('log_file', '未知')
        
        # 检查进程是否还在运行
        try:
            os.kill(pid, 0)
            status = '运行中'
        except (OSError, ProcessLookupError):
            status = '已停止 (僵尸状态)'
        
        print(f'模块: {module}')
        print(f'  状态: {status}')
        print(f'  PID: {pid}')
        print(f'  启动时间: {started}')
        print(f'  日志文件: {log_file}')
        
        # 显示日志最后几行
        if Path(log_file).exists():
            try:
                lines = open(log_file, 'r', encoding='utf-8', errors='ignore').readlines()
                if lines:
                    print(f'  最新日志:')
                    for line in lines[-3:]:
                        print(f'    {line.strip()[:80]}')
            except Exception:
                pass
        print()
    except Exception as e:
        print(f'{module}: 读取失败 - {e}')

if not found_any:
    print('[i] 暂无运行中的模块')
    print()
    print('启动模块命令:')
    print('  start_module.bat presales    - 启动售前')
    print('  start_module.bat operations  - 启动运营')
    print('  start_module.bat aftersales  - 启动售后')
"

echo.
pause
exit /b 0

:CHECK_MODULE
set "MODULE=%~1"
set "NAME=%~2"
set "STATE_FILE=data\module_runtime\%MODULE%.json"

if exist "%STATE_FILE%" (
    for /f "tokens=*" %%a in ('.venv\Scripts\python -c "import json; d=json.load(open('%STATE_FILE%')); print(d['pid'])" 2^>nul') do set "PID=%%a"
    
    :: 检查进程是否存在
    .venv\Scripts\python -c "import os; os.kill(int('!PID!'), 0)" 2>nul
    if errorlevel 1 (
        echo [✗] %NAME%: 僵尸状态 (PID: !PID!)
    ) else (
        echo [✓] %NAME%: 运行中 (PID: !PID!)
    )
) else (
    echo [○] %NAME%: 未运行
)
goto :EOF
