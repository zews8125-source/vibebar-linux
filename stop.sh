#!/usr/bin/env bash
# ==============================================================================
# stop.sh - Остановка всех процессов VibeBar
# ==============================================================================

echo "Остановка VibeBar..."
pkill -f "vibebar-applet.py" 2>/dev/null || true
pkill -f "vibebar-clipboard.py" 2>/dev/null || true
rm -f /tmp/vibebar_recording.pid /tmp/vibebar_record.wav

echo "VibeBar остановлен."
