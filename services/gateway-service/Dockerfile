FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制共享库和安装依赖
COPY services/common /tmp/common
COPY services/gateway-service/pyproject.toml /app/
COPY services/gateway-service/app /app/app

# 安装依赖
RUN pip install --no-cache-dir -e /tmp/common && \
    pip install --no-cache-dir fastapi>=0.104 uvicorn[standard]>=0.24 httpx>=0.25

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "app.main"]
