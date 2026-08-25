#!/usr/bin/env bash
# ==============================================================================
# VibeBar Universal Multi-User Linux Installer
# Поддерживает установку в /opt/vibebar или в $HOME/.local/share/vibebar
# ==============================================================================

set -e

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_USER="${SUDO_USER:-$USER}"
USER_HOME=$(eval echo "~$CURRENT_USER")

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   Универсальный установщик VibeBar для Linux        ${NC}"
echo -e "${BLUE}======================================================${NC}"

# 1. Выбор директории установки
DEFAULT_INSTALL_DIR="/opt/vibebar"
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Примечание: Для установки в /opt/vibebar требуются права sudo.${NC}"
    echo -e "Если запустить без sudo, установка будет выполнена в: ${GREEN}$USER_HOME/.local/share/vibebar${NC}"
    read -p "Установить в [$USER_HOME/.local/share/vibebar] или указать другой путь? (Enter для пути по умолчанию): " USER_CHOICE_DIR
    INSTALL_DIR="${USER_CHOICE_DIR:-$USER_HOME/.local/share/vibebar}"
else
    read -p "Директория установки [по умолчанию $DEFAULT_INSTALL_DIR]: " USER_CHOICE_DIR
    INSTALL_DIR="${USER_CHOICE_DIR:-$DEFAULT_INSTALL_DIR}"
fi

# Раскрываем ~ если пользователь ввел с тильдой
INSTALL_DIR=$(eval echo "$INSTALL_DIR")

echo -e "\n${GREEN}Целевая директория:${NC} $INSTALL_DIR"
echo -e "${GREEN}Пользователь:${NC} $CURRENT_USER (Home: $USER_HOME)\n"

# 2. Создание директории и копирование исходников
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/bin"

echo "[1/5] Копирование компонентов VibeBar..."
cp -r "$SCRIPT_DIR/../bin/"* "$INSTALL_DIR/bin/"
cp "$SCRIPT_DIR/config/config.env.example" "$INSTALL_DIR/config.env"
cp "$SCRIPT_DIR/../requirements.txt" "$INSTALL_DIR/requirements.txt"

# 3. Установка системных зависимостей (apt если доступен)
if command -v apt-get >/dev/null 2>&1; then
    echo "[2/5] Проверка системных пакетов (apt)..."
    if [ "$EUID" -eq 0 ]; then
        apt-get update -qq || true
        apt-get install -y -qq python3-pip python3-venv python3-gi gir1.2-ayatanaappindicator3-0.1 alsa-utils xdotool libcanberra-gtk-module >/dev/null 2>&1 || true
    else
        echo "Пропуск apt-get (не root). Убедитесь, что установлены alsa-utils, xdotool, python3-gi."
    fi
fi

# 4. Создание изолированного Python venv
echo "[3/5] Создание виртуального окружения Python..."
python3 -m venv --system-site-packages "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q

# Делаем скрипты исполняемыми
chmod +x "$INSTALL_DIR/bin/"*.sh "$INSTALL_DIR/bin/"*.py 2>/dev/null || true

# 5. Создание симлинков для быстрого запуска в /usr/local/bin или ~/.local/bin
BIN_TARGET="/usr/local/bin"
if [ "$EUID" -ne 0 ] || [ ! -w "/usr/local/bin" ]; then
    BIN_TARGET="$USER_HOME/.local/bin"
    mkdir -p "$BIN_TARGET"
fi

echo "[4/5] Создание исполняемых команд в $BIN_TARGET..."

# Обертка для записи
cat <<EOF > "$BIN_TARGET/vibebar-record"
#!/usr/bin/env bash
exec "$INSTALL_DIR/bin/vibebar-record.sh" "\$@"
EOF
chmod +x "$BIN_TARGET/vibebar-record"

# Обертка для старта
cat <<EOF > "$BIN_TARGET/vibebar-start"
#!/usr/bin/env bash
pkill -f "$INSTALL_DIR/bin/vibebar-applet.py" 2>/dev/null || true
pkill -f "$INSTALL_DIR/bin/vibebar-clipboard.py" 2>/dev/null || true
sleep 0.3
"$INSTALL_DIR/.venv/bin/python3" "$INSTALL_DIR/bin/vibebar-applet.py" >/tmp/vibebar_applet.log 2>&1 &
"$INSTALL_DIR/.venv/bin/python3" "$INSTALL_DIR/bin/vibebar-clipboard.py" >/tmp/vibebar_clipboard.log 2>&1 &
echo "VibeBar успешно запущен!"
EOF
chmod +x "$BIN_TARGET/vibebar-start"

# Обертка для остановки
cat <<EOF > "$BIN_TARGET/vibebar-stop"
#!/usr/bin/env bash
pkill -f "$INSTALL_DIR/bin/vibebar-applet.py" 2>/dev/null || true
pkill -f "$INSTALL_DIR/bin/vibebar-clipboard.py" 2>/dev/null || true
rm -f /tmp/vibebar_recording.pid /tmp/vibebar_record.wav
echo "VibeBar остановлен."
EOF
chmod +x "$BIN_TARGET/vibebar-stop"

# Если ставили от root, выставляем правильного владельца
if [ "$EUID" -eq 0 ]; then
    chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"
fi

echo "[5/5] Настройка завершена!"

echo -e "\n${GREEN}==================================================================${NC}"
echo -e "${GREEN}   VIBEBAR УСПЕШНО УСТАНОВЛЕН В: $INSTALL_DIR                    ${NC}"
echo -e "${GREEN}==================================================================${NC}"
echo -e "Команды быстрого управления:"
echo -e "  - Запуск:    ${YELLOW}vibebar-start${NC} (или $INSTALL_DIR/bin/vibebar-applet.py)"
echo -e "  - Остановка: ${YELLOW}vibebar-stop${NC}"
echo -e "  - Запись:    ${YELLOW}vibebar-record${NC}"
echo -e "\nДля привязки глобальной горячей клавиши (например F9):"
echo -e "  Укажите команду: ${GREEN}$BIN_TARGET/vibebar-record${NC}"
echo -e "=================================================================="
