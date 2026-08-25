#!/usr/bin/env bash
# ==============================================================================
# VibeBar Linux - Установщик и настройщик окружения
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "    Установка VibeBar для Linux Mint / Ubuntu     "
echo "=================================================="

# 1. Создание venv если еще нет
if [ ! -d ".venv" ]; then
    echo "[1/4] Создание Python окружения (.venv)..."
    python3 -m venv --system-site-packages .venv
fi

# 2. Установка зависимостей
echo "[2/4] Проверка и установка зависимостей..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# 3. Делаем бинарники исполняемыми
chmod +x bin/vibebar-*.sh bin/vibebar-*.py

# 4. Настройка автозапуска
echo "[3/4] Настройка автозапуска в системе..."
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat <<EOF > "$AUTOSTART_DIR/vibebar.desktop"
[Desktop Entry]
Type=Application
Exec=$SCRIPT_DIR/.venv/bin/python3 $SCRIPT_DIR/bin/vibebar-applet.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=VibeBar
Comment=Голосовой трекер задач и менеджер буфера обмена
Icon=audio-input-microphone
Categories=Utility;Productivity;
EOF

cat <<EOF > "$AUTOSTART_DIR/vibebar-clipboard.desktop"
[Desktop Entry]
Type=Application
Exec=$SCRIPT_DIR/.venv/bin/python3 $SCRIPT_DIR/bin/vibebar-clipboard.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=VibeBar Clipboard Daemon
Comment=Служба буфера обмена для VibeBar
Icon=edit-copy
Categories=Utility;
EOF

echo "[4/4] Готово!"
echo ""
echo "=================================================================="
echo "  НАСТРОЙКА ГОРЯЧЕЙ КЛАВИШИ В LINUX MINT:"
echo "  1. Откройте: Настройки системы -> Клавиатура -> Комбинации клавиш"
echo "  2. Перейдите в 'Дополнительные комбинации' (Custom Shortcuts)"
echo "  3. Нажмите 'Добавить':"
echo "     - Название: VibeBar Record"
echo "     - Команда:  $SCRIPT_DIR/bin/vibebar-record.sh"
echo "  4. Назначьте комбинацию (например Ctrl+Alt+V или Super+Space)"
echo "=================================================================="
