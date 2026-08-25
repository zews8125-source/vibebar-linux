#!/usr/bin/env bash
# ==============================================================================
# vibebar-record.sh
# Toggle скрипт записи голоса:
# 1-й вызов -> старт записи arecord, сохранение PID, уведомление
# 2-й вызов -> стоп записи, отправка в vibebar-stt.py -> vibebar-add.py -> уведомление
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/config.env"

# Подгрузка конфигурации
if [ -f "$CONFIG_FILE" ]; then
    set -a
    source "$CONFIG_FILE"
    set +a
fi

PID_FILE="/tmp/vibebar_recording.pid"
AUDIO_FILE="/tmp/vibebar_record.wav"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python3"
if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="python3"
fi

play_beep() {
    # Короткий системный звук если включен
    if [ "${VIBEBAR_SOUND_NOTIFICATIONS:-1}" = "1" ]; then
        paplay /usr/share/sounds/freedesktop/stereo/message.oga 2>/dev/null || \
        paplay /usr/share/sounds/freedesktop/stereo/bell.oga 2>/dev/null || \
        canberra-gtk-play -i audio-volume-change 2>/dev/null || true
    fi
}

# 1. Проверяем, идет ли сейчас запись
if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE" 2>/dev/null) 2>/dev/null; then
    # --- ОСТАНОВКА ЗАПИСИ ---
    RECORD_PID=$(cat "$PID_FILE")
    kill -15 "$RECORD_PID" 2>/dev/null || kill -9 "$RECORD_PID" 2>/dev/null
    rm -f "$PID_FILE"
    play_beep
    
    notify-send "VibeBar" "⏳ Распознаю голос..." -i microphone-sensitivity-low -t 2000

    if [ -f "$AUDIO_FILE" ]; then
        # Вызываем STT
        TRANSCRIBED_TEXT=$("$VENV_PYTHON" "$SCRIPT_DIR/vibebar-stt.py" "$AUDIO_FILE" 2>/tmp/vibebar_stt_err.log)
        
        if [ -n "$TRANSCRIBED_TEXT" ]; then
            # Добавляем в журнал через классификатор
            "$VENV_PYTHON" "$SCRIPT_DIR/vibebar-add.py" "$TRANSCRIBED_TEXT"
            notify-send "VibeBar: Запись добавлена" "$TRANSCRIBED_TEXT" -i emblem-default -t 4000
        else
            notify-send "VibeBar" "Голос не распознан или тишина" -i dialog-warning -t 3000
        fi
    fi
else
    # --- СТАРТ ЗАПИСИ ---
    rm -f "$PID_FILE" "$AUDIO_FILE"
    play_beep
    
    # 16kHz, 16-bit Mono - оптимальный формат для Whisper / Parakeet
    arecord -f S16_LE -c 1 -r 16000 -t wav "$AUDIO_FILE" >/dev/null 2>&1 &
    echo $! > "$PID_FILE"
    
    notify-send "VibeBar" "🎙️ Запись пошла... (нажмите еще раз для стопа)" -i microphone-sensitivity-high -t 3000
fi
