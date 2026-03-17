@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

:: ===========================================
::   闲鱼管家 - Windows 桌面快捷方式安装
:: ===========================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\.."
set "PROJECT_DIR=%CD%"

echo.
echo =========================================
echo   闲鱼管家 - 桌面快捷方式安装
echo =========================================
echo.

:: 创建启动批处理文件
set "START_BAT=%PROJECT_DIR%\scripts\windows\start-desktop.bat"

:: 创建桌面快捷方式（使用 PowerShell 创建 .lnk）
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\闲鱼管家.lnk"

echo [*] 创建桌面快捷方式...

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $sc = $ws.CreateShortcut('%SHORTCUT%'); ^
   $sc.TargetPath = '%PROJECT_DIR%\start.bat'; ^
   $sc.WorkingDirectory = '%PROJECT_DIR%'; ^
   $sc.Description = '闲鱼管家 - 自动化工作台'; ^
   $sc.Save()"

if exist "%SHORTCUT%" (
    echo [OK] 已在桌面创建「闲鱼管家」快捷方式
    echo      双击即可启动所有服务
) else (
    echo [!!] 快捷方式创建失败，请手动将 start.bat 拖到桌面
)

echo.

:: 询问是否添加开机自启动
set /p ADD_STARTUP="是否添加开机自启动？(y/N): "
if /i "%ADD_STARTUP%"=="y" goto :INSTALL_STARTUP
goto :DONE

:INSTALL_STARTUP
echo.
echo [*] 正在设置开机自启动...

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "STARTUP_SHORTCUT=%STARTUP_DIR%\闲鱼管家.lnk"

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $sc = $ws.CreateShortcut('%STARTUP_SHORTCUT%'); ^
   $sc.TargetPath = '%PROJECT_DIR%\start.bat'; ^
   $sc.WorkingDirectory = '%PROJECT_DIR%'; ^
   $sc.WindowStyle = 7; ^
   $sc.Description = '闲鱼管家 - 开机自启动'; ^
   $sc.Save()"

if exist "%STARTUP_SHORTCUT%" (
    echo [OK] 已添加开机自启动
    echo      位置: %STARTUP_SHORTCUT%
    echo      如需取消，删除该文件即可
) else (
    echo [!!] 开机自启动设置失败
)

:DONE
echo.
echo =========================================
echo   安装完成
echo =========================================
echo.
pause
