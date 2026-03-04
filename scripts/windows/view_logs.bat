@echo off
chcp 65001 >nul
title 查看日志
color 0E

:: ========================================
:: 查看日志脚本
:: ========================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\.."

set "MODULE=%~1"
set "LINES=%~2"

if "%MODULE%"=="" set "MODULE=all"
if "%LINES%"=="" set "LINES=50"

echo.
echo ===========================================
echo    查看日志: %MODULE%
echo ===========================================
echo.

if "%MODULE%"=="all" (
    :: 显示所有日志
    for %%m in (presales operations aftersales) do (
        call :SHOW_LOG %%m %LINES%
        echo.
    )
) else (
    call :SHOW_LOG %MODULE% %LINES%
)

echo.
echo [i] 提示: 使用 %~nx0 [模块名] [行数] 可查看指定日志
echo     例如: %~nx0 presales 100
echo.
pause
exit /b 0

:SHOW_LOG
set "LOG_MODULE=%~1"
set "LOG_LINES=%~2"
set "LOG_FILE=logs\%LOG_MODULE%.log"

echo --- %LOG_MODULE% 日志 (最后 %LOG_LINES% 行) ---
echo.

if exist "%LOG_FILE%" (
    powershell -Command "Get-Content -Path '%LOG_FILE%' -Tail %LOG_LINES%"
) else (
    echo [i] 暂无日志文件: %LOG_FILE%
)

goto :EOF
