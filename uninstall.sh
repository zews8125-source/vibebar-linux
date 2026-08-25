#!/usr/bin/env bash
# ==============================================================================
# VibeBar Linux - Скрипт удаления
# ==============================================================================

echo "Удаление VibeBar автозапуска..."
rm -f "$HOME/.config/autostart/vibebar.desktop"
rm -f "$HOME/.config/autostart/vibebar-clipboard.desktop"
rm -f /tmp/vibebar_recording.pid /tmp/vibebar_record.wav

echo "Остановка процессов..."
pkill -f "vibebar-applet.py" 2>/dev/null || true
pkill -f "vibebar-clipboard.py" 2>/dev/null || true

echo "VibeBar успешно деактивирован."
