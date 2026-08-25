# VibeBar Universal Multi-PC Installer 🚀

Пакет для автоматической установки **VibeBar** на любой компьютер с **Linux (Linux Mint / Cinnamon / Ubuntu / Debian)**.

---

## 💻 Установка на любом компьютере

### Вариант 1: Системная установка в `/opt/vibebar` (Рекомендуется, с `sudo`)
```bash
sudo ./install.sh
```
- Устанавливает VibeBar в `/opt/vibebar`.
- Создает общесистемные команды в `/usr/local/bin`: `vibebar-start`, `vibebar-stop`, `vibebar-record`.
- Файлы пользователя (`~/vibebar-journal.md` и `~/vibebar-clipboard.json`) сохраняются строго в домашней директории текущего пользователя.

### Вариант 2: Пользовательская установка без `sudo`
```bash
./install.sh
```
- Устанавливает VibeBar в `~/.local/share/vibebar` без необходимости ввода root-пароля.
- Создает команды в `~/.local/bin`.

---

## ⌨️ Настройка горячей клавиши на целевом компьютере

1. Откройте **Параметры системы** ➔ **Клавиатура** ➔ **Комбинации клавиш**.
2. Перейдите в **Дополнительные комбинации клавиш** (Custom Shortcuts).
3. Нажмите **Добавить**:
   - **Название:** `VibeBar Record`
   - **Команда:** `vibebar-record`
4. Назначьте удобную клавишу (например, **F9** или `Ctrl+Alt+V`).

---

## 🛠️ Управление

- **Запуск:** `vibebar-start`
- **Остановка:** `vibebar-stop`
- **Удаление:** `sudo ./uninstall.sh` (или `./uninstall.sh`)
