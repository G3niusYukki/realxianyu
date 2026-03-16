@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\.."
set "PROJECT_DIR=%CD%"
set "BROWSERS_DIR=%PROJECT_DIR%\.playwright-browsers"
set "DIST_DIR=%PROJECT_DIR%\dist"
set "ARCHIVE_DIR=%DIST_DIR%\xianyu-openclaw-offline"

echo.
echo =========================================
echo   Prepare Offline Playwright Bundle
echo =========================================
echo.
echo [INFO] Project directory: %PROJECT_DIR%

if not exist ".venv\Scripts\python.exe" (
    echo [*] Creating Python virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        exit /b 1
    )
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    exit /b 1
)

echo [*] Installing Python dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    exit /b 1
)

echo [*] Installing Node.js dependencies...
if not exist "server\node_modules" (
    cd server && npm install --silent && cd ..
    if errorlevel 1 (
        echo [ERROR] Failed to install server dependencies
        exit /b 1
    )
)
if not exist "client\node_modules" (
    cd client && npm install --silent && cd ..
    if errorlevel 1 (
        echo [ERROR] Failed to install client dependencies
        exit /b 1
    )
)

set "PLAYWRIGHT_BROWSERS_PATH=%BROWSERS_DIR%"
echo [*] Downloading Playwright Chromium into %PLAYWRIGHT_BROWSERS_PATH% ...
.venv\Scripts\playwright install chromium
if errorlevel 1 (
    echo [ERROR] Failed to download Playwright Chromium
    exit /b 1
)

echo [*] Verifying bundled browser...
.venv\Scripts\python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(headless=True); b.close(); p.stop()"
if errorlevel 1 (
    echo [ERROR] Bundled Playwright Chromium verification failed
    exit /b 1
)

if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"
if exist "%ARCHIVE_DIR%" rmdir /s /q "%ARCHIVE_DIR%"
mkdir "%ARCHIVE_DIR%"

echo [*] Copying project files...
xcopy "%PROJECT_DIR%" "%ARCHIVE_DIR%" /E /I /H /Y /EXCLUDE:%SCRIPT_DIR%pack_offline_playwright.exclude >nul
if errorlevel 1 (
    echo [ERROR] Failed to copy project files
    exit /b 1
)

echo.
echo [OK] Offline bundle prepared: %ARCHIVE_DIR%
echo [OK] Copy this folder to the offline Windows machine and run start.bat
echo [OK] Project-local browser path: %ARCHIVE_DIR%\.playwright-browsers
echo.
exit /b 0
