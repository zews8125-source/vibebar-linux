#!/usr/bin/env bash
# ==============================================================================
# start.sh - Ручной запуск VibeBar для тестирования и работы
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Запуск VibeBar..."

# Останавливаем старые копии, если были запущены
pkill -f "vibebar-applet.py" 2>/dev/null || true
pkill -f "vibebar-clipboard.py" 2>/dev/null || true
sleep 0.5

# Запуск апплета и демона буфера в фоновом режиме
.venv/bin/python3 bin/vibebar-applet.py >/tmp/vibebar_applet.log 2>&1 &
APPLET_PID=$!

.venv/bin/python3 bin/vibebar-clipboard.py >/tmp/vibebar_clipboard.log 2>&1 &
CLIP_PID=$!

echo "=================================================="
echo "  VibeBar запущен!"
echo "  - Апплет трея (PID: $APPLET_PID)"
echo "  - Демон буфера (PID: $CLIP_PID)"
echo "  - Логи: /tmp/vibebar_applet.log"
echo "=================================================="
echo "Для остановки выполните: ./stop.sh"
