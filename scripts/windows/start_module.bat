@echo off
chcp 65001 >nul
title 启动模块
color 0E

:: ========================================
:: 模块启动脚本
:: 支持: presales, operations, aftersales
:: ========================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\.."

set "MODULE=%~1"
set "MODE=%~2"
set "LIMIT=%~3"
set "INTERVAL=%~4"

if "%MODULE%"=="" (
    echo [!] 错误: 未指定模块
    echo 用法: %~nx0 [presales^|operations^|aftersales] [daemon^|foreground] [limit] [interval]
    exit /b 1
)

:: 默认值
if "%MODE%"=="" set "MODE=daemon"
if "%LIMIT%"=="" set "LIMIT=20"
if "%INTERVAL%"=="" set "INTERVAL=5"

echo.
echo ===========================================
echo    启动模块: %MODULE%
echo ===========================================
echo.

:: 检查虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo [!] 未检测到虚拟环境，请先运行 install.bat
    pause
    exit /b 1
)

:: 检查配置文件
if not exist ".env" (
    echo [!] 未检测到配置文件，请先运行 simple_config.bat
    pause
    exit /b 1
)

:: 检查是否已在运行
if exist "data\module_runtime\%MODULE%.json" (
    .venv\Scripts\python -c "import json,sys; d=json.load(open('data/module_runtime/%MODULE%.json')); print(f'[i] 模块已在运行 (PID: {d[\"pid\"]})')" 2>nul
    echo.
    echo 选项:
    echo  [1] 停止当前实例并重新启动
    echo  [2] 保持当前运行，取消操作
    echo.
    set /p choice="请选择 (1-2): "
    if "!choice!"=="1" (
        call "%SCRIPT_DIR%stop_module.bat" %MODULE%
    ) else (
        echo [*] 取消启动
        exit /b 0
    )
)

:: 创建日志目录
mkdir logs 2>nul
mkdir data\module_runtime 2>nul

echo [*] 正在启动 %MODULE% 模块...
echo     模式: %MODE%
echo     限制: %LIMIT%
echo     间隔: %INTERVAL%秒

:: 根据模块类型设置不同参数
set "EXTRA_ARGS="
if "%MODULE%"=="presales" (
    set "EXTRA_ARGS=--transport ws"
)
if "%MODULE%"=="aftersales" (
    set "EXTRA_ARGS=--issue-type delay"
)

:: 启动模块
if "%MODE%"=="daemon" (
    :: 后台模式 - 使用Python在后台运行
    .venv\Scripts\python -c "
import subprocess, sys, os, json, time
from pathlib import Path

module = '%MODULE%'
log_file = Path(f'logs/{module}.log')
log_file.parent.mkdir(exist_ok=True)

# 构建启动命令
cmd = [
    sys.executable, '-m', 'src.cli', 'module',
    '--action', 'start',
    '--target', module,
    '--mode', 'daemon',
    '--limit', '%LIMIT%',
    '--interval', '%INTERVAL%'
]

# 后台运行
with open(log_file, 'a', encoding='utf-8') as f:
    proc = subprocess.Popen(
        cmd,
        stdout=f,
        stderr=subprocess.STDOUT,
        cwd=os.getcwd(),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    
# 保存状态
state = {
    'target': module,
    'pid': proc.pid,
    'log_file': str(log_file),
    'started_at': time.strftime('%%Y-%%m-%%dT%%H:%%M:%%S')
}
Path('data/module_runtime').mkdir(parents=True, exist_ok=True)
with open(f'data/module_runtime/{module}.json', 'w') as f:
    json.dump(state, f, indent=2)

print(f'[✓] 模块已启动 (PID: {proc.pid})')
print(f'[i] 日志: {log_file}')
"
    if errorlevel 1 (
        echo [!] 启动失败
        pause
        exit /b 1
    )
) else (
    :: 前台模式 - 直接运行
    echo [*] 前台运行模式 (按Ctrl+C停止)
    echo.
    .venv\Scripts\python -m src.cli module --action start --target %MODULE% --mode foreground --limit %LIMIT% --interval %INTERVAL% %EXTRA_ARGS%
)

echo.
echo [✓] 启动完成！
echo.
pause
exit /b 0
