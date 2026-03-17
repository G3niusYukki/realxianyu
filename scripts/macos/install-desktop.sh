#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DESKTOP="$HOME/Desktop"

echo ""
echo "========================================="
echo "  闲鱼管家 - macOS 桌面快捷方式安装"
echo "========================================="
echo ""

chmod +x "$SCRIPT_DIR/start.command" 2>/dev/null || true

if [ -d "$DESKTOP" ]; then
    # 动态生成 .command 文件，写入实际的项目绝对路径
    cat > "$DESKTOP/闲鱼管家.command" << CMDEOF
#!/usr/bin/env bash
# 闲鱼管家 - 桌面一键启动（由 install-desktop.sh 生成）
# 项目路径: $PROJECT_ROOT

cd "$PROJECT_ROOT"

if [ -f "start.sh" ]; then
    exec bash start.sh
else
    exec bash scripts/macos/start.command
fi
CMDEOF
    chmod +x "$DESKTOP/闲鱼管家.command"
    echo "[OK] 已在桌面创建「闲鱼管家.command」"
    echo "     双击即可启动所有服务"
    echo "     项目路径: $PROJECT_ROOT"
else
    echo "[!!] 未找到桌面目录: $DESKTOP"
fi

echo ""
read -p "是否添加开机自启动 (LaunchAgent)？(y/N): " ADD_AUTOSTART
if [[ "$ADD_AUTOSTART" =~ ^[Yy]$ ]]; then
    if [ -f "$PROJECT_ROOT/scripts/install-launchd.sh" ]; then
        bash "$PROJECT_ROOT/scripts/install-launchd.sh"
    elif [ -f "$SCRIPT_DIR/install_service.sh" ]; then
        bash "$SCRIPT_DIR/install_service.sh" install
    else
        echo "[!!] 未找到 LaunchAgent 安装脚本"
    fi
else
    echo "[OK] 跳过开机自启动"
fi

echo ""
echo "========================================="
echo "  安装完成"
echo "========================================="
echo ""
