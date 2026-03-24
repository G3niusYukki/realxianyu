# XianyuFlow | 闲流 - Agent Deployment Guide

This document is specifically designed for AI Agents (like GitHub Copilot, Gemini Code Assist, or Claude) to understand how to deploy and run this project. All legacy one-click `.bat`/`.sh` scripts have been removed in favor of standard Node.js and Python deployment practices.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Quick Start](#2-quick-start)
3. [Frontend Build](#3-frontend-build)
4. [Backend Setup](#4-backend-setup)
5. [Configuration](#5-configuration)
6. [Starting the Service](#6-starting-the-service)
7. [Troubleshooting](#7-troubleshooting)
8. [Platform-Specific Notes](#8-platform-specific-notes)
9. [Architecture Overview](#9-architecture-overview)

---

## 1. Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.12+ | Required for backend |
| **Node.js** | 18+ | Required for frontend build |
| **npm** | 9+ | Comes with Node.js |
| **Chrome/Edge** | Latest | For Playwright automation |

### Verify Prerequisites

```bash
# Check Python version
python3 --version  # Should show 3.12.x or higher

# Check Node.js version
node --version     # Should show v18.x.x or higher

# Check npm version
npm --version      # Should show 9.x.x or higher
```

---

## 2. Quick Start

For AI agents, follow this exact sequence:

```bash
# Step 1: Clone and enter directory
git clone https://github.com/G3niusYukki/realxianyu.git
cd realxianyu

# Step 2: Build frontend
cd client && npm install && npm run build && cd ..

# Step 3: Setup Python environment
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Step 4: Configure environment
cp .env.example .env
# Edit .env with required variables (see Configuration section)

# Step 5: Start service
python -m src.main
```

The dashboard will be available at `http://localhost:8080` (or your configured PORT).

---

## 3. Frontend Build (Required)

The project uses a separated frontend built with React, Vite, and Tailwind. The backend serves the compiled static files from `client/dist`.

```bash
cd client
npm install
npm run build
```

**Important:** If `client/dist` does not exist, the backend will return a 404 or an error page when accessing the dashboard.

### Common Frontend Build Issues

#### Issue: npm install fails with EACCES
**Solution:**
```bash
# Fix npm permissions
sudo chown -R $(whoami) ~/.npm
# Or use npx
npx --yes npm install
```

#### Issue: Node.js version mismatch
**Solution:**
```bash
# Use nvm to switch versions (if available)
nvm use 18
# Or install specific version
npm install -g n
n 18
```

#### Issue: Vite build fails with OOM
**Solution:**
```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

---

## 4. Backend Setup

The backend is a pure Python application using standard library HTTP servers and Asyncio.

```bash
# Return to project root
cd ..

# Create and activate virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# (Optional) Install Playwright browsers if slider auto-solve is needed
playwright install chromium
```

### Common Backend Setup Issues

#### Issue: Python version not found
**Solution:**
```bash
# macOS with Homebrew
brew install python@3.12

# Ubuntu/Debian
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-pip

# Verify
python3.12 --version
```

#### Issue: pip install fails with SSL/TLS errors
**Solution:**
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Or use trusted hosts (not recommended for production)
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

#### Issue: Package conflicts during installation
**Solution:**
```bash
# Clear pip cache
pip cache purge

# Force reinstall
pip install -r requirements.txt --force-reinstall
```

---

## 5. Configuration

The system requires a `.env` file in the root directory. Copy the example file and fill in the necessary keys.

```bash
cp .env.example .env
```

### Required `.env` Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PORT` | No | Dashboard port (default: 8080) |
| `XIANYU_COOKIE_1` | Yes | Essential for connecting to Xianyu |
| `DEEPSEEK_API_KEY` | Yes* | For message auto-reply (*or other AI provider) |
| `COOKIE_CLOUD_URL` | No | For automatic cookie syncing |
| `COOKIE_CLOUD_UUID` | No | CookieCloud UUID |
| `COOKIE_CLOUD_PASSWORD` | No | CookieCloud password |

### AI Provider Options

You can use any of these AI providers:

```bash
# DeepSeek (Recommended)
AI_PROVIDER=deepseek
AI_API_KEY=sk-...
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat

# Alibaba Bailian
AI_PROVIDER=aliyun_bailian
AI_API_KEY=sk-...
AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_MODEL=qwen-plus

# OpenAI
AI_PROVIDER=openai
AI_API_KEY=sk-...
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
```

---

## 6. Starting the Service

Start the main backend service. It will automatically load `.env` and serve the API routes and the compiled frontend dashboard.

```bash
python -m src.main
```

The dashboard will be available at `http://localhost:<PORT>` (default `http://localhost:8080`).

### Service Management

```bash
# Run in background (Linux/macOS)
python -m src.main &

# Check if running
curl http://localhost:8080/healthz

# Stop service
pkill -f "python -m src.main"
```

---

## 7. Troubleshooting

### 7.1 Port Already in Use

```bash
# Find process using port
lsof -ti:8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Kill process
kill -9 $(lsof -ti:8080)  # macOS/Linux
taskkill /PID <PID> /F     # Windows

# Or change port in .env
PORT=8081
```

### 7.2 Frontend 404 Error

If you see a 404 when accessing the dashboard:

```bash
# Rebuild frontend
cd client
npm install
npm run build
cd ..

# Verify dist folder exists
ls -la client/dist/
```

### 7.3 Cookie Authentication Failed

```bash
# Test cookie validity
curl -H "Cookie: $(grep XIANYU_COOKIE_1 .env | cut -d= -f2)" https://www.goofish.com

# Check logs
tail -f logs/app.log
```

### 7.4 Database Locked

```bash
# Remove lock file
rm data/*.db-journal data/*.db-wal data/*.db-shm

# Or reset database (WARNING: data loss)
rm data/agent.db
```

### 7.5 Module Import Errors

```bash
# Ensure you're in the correct directory
pwd  # Should show /path/to/realxianyu

# Verify virtual environment is activated
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### 7.6 Playwright Browser Not Found

```bash
# Reinstall Playwright browsers
playwright install chromium

# Or install all browsers
playwright install

# Check browser installation
playwright chromium --version
```

---

## 8. Platform-Specific Notes

### macOS

```bash
# Install dependencies with Homebrew
brew install python@3.12 node

# If you get SSL certificate errors
export SSL_CERT_FILE=$(python -m certifi)

# For Apple Silicon (M1/M2/M3)
arch -arm64 brew install python@3.12
```

### Linux (Ubuntu/Debian)

```bash
# Install Python 3.12
sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### Windows

```powershell
# Run PowerShell as Administrator

# Install Python from Microsoft Store or python.org
# Install Node.js from nodejs.org

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Build frontend
cd client
npm install
npm run build
cd ..

# Start service
python -m src.main
```

---

## 9. Architecture Overview

- **Frontend:** `client/src/`
- **Backend Entry:** `src/main.py` -> `src/dashboard_server.py`
- **Routes:** `src/dashboard/routes/`
- **Business Logic:** `src/modules/` and `src/services/`
- **Configuration:** `.env`, `config/config.yaml`, `data/system_config.json`

### Key Files for AI Agents

| File | Purpose |
|------|---------|
| `src/main.py` | Application entry point |
| `src/dashboard/mimic_ops.py` | Business logic facade |
| `src/core/config.py` | Configuration management |
| `client/src/App.tsx` | Frontend entry |
| `.env.example` | Environment template |

---

## Verification Checklist

After deployment, verify:

- [ ] Frontend built successfully (`client/dist/` exists)
- [ ] Backend starts without errors
- [ ] Health check returns 200: `curl http://localhost:8080/healthz`
- [ ] Dashboard accessible at `http://localhost:8080`
- [ ] Cookie configured in `.env`
- [ ] AI provider configured (if using auto-reply)

---

**Last Updated:** 2026-03-24  
**Version:** 9.5.0  
**Maintainer:** Project Team
