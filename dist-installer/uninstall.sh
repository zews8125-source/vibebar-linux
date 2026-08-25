#!/usr/bin/env bash
# ==============================================================================
# VibeBar Universal Uninstaller
# ==============================================================================

set -e

CURRENT_USER="${SUDO_USER:-$USER}"
USER_HOME=$(eval echo "~$CURRENT_USER")

INSTALL_DIR="/opt/vibebar"
if [ ! -d "$INSTALL_DIR" ]; then
    INSTALL_DIR="$USER_HOME/.local/share/vibebar"
fi

echo "Остановка VibeBar..."
pkill -f "vibebar-applet.py" 2>/dev/null || true
pkill -f "vibebar-clipboard.py" 2>/dev/null || true
rm -f /tmp/vibebar_recording.pid /tmp/vibebar_record.wav

echo "Удаление исполняемых команд..."
rm -f "/usr/local/bin/vibebar-record" "/usr/local/bin/vibebar-start" "/usr/local/bin/vibebar-stop" 2>/dev/null || true
rm -f "$USER_HOME/.local/bin/vibebar-record" "$USER_HOME/.local/bin/vibebar-start" "$USER_HOME/.local/bin/vibebar-stop" 2>/dev/null || true

if [ -d "$INSTALL_DIR" ]; then
    echo "Удаление директории $INSTALL_DIR..."
    rm -rf "$INSTALL_DIR"
fi

echo "VibeBar успешно удален."
