#!/usr/bin/env python3
"""
vibebar-applet.py
Главный GUI апплет VibeBar в трее Linux Mint / Cinnamon:
 - Поддержка AyatanaAppIndicator3 / AppIndicator3
 - Отображение текущей задачи и живого бегущего таймера
 - Интерактивное меню:
    * Текущая задача + таймер
    * 💡 Идеи за сегодня (клик копирует)
    * ❗ Напоминания (интерактивный чекбокс с обновлением Markdown)
    * 📋 Буфер обмена (последние 15 элементов + автовставка через xdotool)
    * ⚙️ Инструменты (Открыть журнал, Сгенерировать сводку, Выход)
"""

import sys
import os
import time
import json
import re
import subprocess
from datetime import datetime

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

# Адаптивный импорт индикатора
try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
except (ValueError, ImportError):
    try:
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3 as AppIndicator
    except (ValueError, ImportError):
        AppIndicator = None

def load_config():
    config = {
        "VIBEBAR_JOURNAL_FILE": os.path.expanduser("~/vibebar-journal.md"),
        "VIBEBAR_CLIPBOARD_FILE": os.path.expanduser("~/vibebar-clipboard.json"),
        "VIBEBAR_AUTOPASTE": "1",
        "VIBEBAR_BUFFER_MAX": "15"
    }
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.env")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"\'')
                v = os.path.expandvars(os.path.expanduser(v))
                config[k] = v
    return config

class VibeBarApplet:
    def __init__(self):
        self.config = load_config()
        self.journal_file = os.path.expanduser(self.config.get("VIBEBAR_JOURNAL_FILE", "~/vibebar-journal.md"))
        self.clipboard_file = os.path.expanduser(self.config.get("VIBEBAR_CLIPBOARD_FILE", "~/vibebar-clipboard.json"))
        self.autopaste = self.config.get("VIBEBAR_AUTOPASTE", "1") == "1"

        self.current_task_title = "Нет активных задач"
        self.current_task_time = None
        self.current_is_pause = False
        self.today_ideas = []
        self.today_reminders = []

        # Создаем иконку индикатора
        icon_name = "audio-input-microphone"
        if AppIndicator:
            self.indicator = AppIndicator.Indicator.new(
                "vibebar-indicator",
                icon_name,
                AppIndicator.IndicatorCategory.APPLICATION_STATUS
            )
            self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        else:
            self.indicator = None

        self.menu = Gtk.Menu()
        self.update_data()
        self.build_menu()

        if self.indicator:
            self.indicator.set_menu(self.menu)

        # Таймер обновления каждую секунду для плавного отсчета
        GLib.timeout_add_seconds(1, self.on_timer_tick)
        # Таймер пересборки меню каждые 5 секунд
        GLib.timeout_add_seconds(5, self.on_menu_refresh_tick)

    def update_data(self):
        """Парсит сегодняшнюю секцию журнала и обновляет состояние."""
        self.today_ideas = []
        self.today_reminders = []
        self.current_task_title = "Нет задач"
        self.current_task_time = None
        self.current_is_pause = False

        if not os.path.exists(self.journal_file):
            return

        today_str = datetime.now().strftime("%Y-%m-%d")
        date_header = f"## {today_str}"
        line_pattern = re.compile(r"^-\s*(\d{1,2}:\d{2})\s*·\s*(.*)$")

        inside_today = False
        last_timeline_event = None

        with open(self.journal_file, "r", encoding="utf-8") as f:
            for line in f:
                l_str = line.strip()
                if l_str.startswith("## "):
                    if l_str == date_header:
                        inside_today = True
                    else:
                        inside_today = False
                    continue

                if not inside_today:
                    continue

                m = line_pattern.match(l_str)
                if m:
                    time_str = m.group(1)
                    content = m.group(2).strip()

                    if content.startswith("💡"):
                        self.today_ideas.append(content[2:].strip())
                    elif content.startswith("❗"):
                        done = "[x]" in content or "[X]" in content
                        clean = re.sub(r"^❗\s*\[[ xX]\]\s*", "", content)
                        self.today_reminders.append({"text": clean, "done": done, "raw": l_str})
                    elif content.startswith("⏸"):
                        last_timeline_event = (time_str, "pause", "Перерыв")
                    else:
                        last_timeline_event = (time_str, "task", content)

        if last_timeline_event:
            t_str, ev_type, title = last_timeline_event
            try:
                self.current_task_time = datetime.strptime(f"{today_str} {t_str}", "%Y-%m-%d %H:%M")
                if ev_type == "pause":
                    self.current_is_pause = True
                    self.current_task_title = "⏸ Перерыв"
                else:
                    self.current_is_pause = False
                    self.current_task_title = title
            except ValueError:
                pass

    def get_timer_label(self) -> str:
        """Возвращает строку для панели трея: [Задача] (ЧЧ:ММ)."""
        if not self.current_task_time or self.current_is_pause:
            return "⏸ Пауза" if self.current_is_pause else "VibeBar"

        diff_sec = max(0, (datetime.now() - self.current_task_time).total_seconds())
        mins = int(diff_sec // 60)
        hours = mins // 60
        rem_mins = mins % 60

        if hours > 0:
            time_formatted = f"{hours}:{rem_mins:02d}"
        else:
            time_formatted = f"0:{rem_mins:02d}"

        short_title = self.current_task_title
        if len(short_title) > 24:
            short_title = short_title[:22] + "…"

        return f"{short_title} ({time_formatted})"

    def on_timer_tick(self):
        label_text = self.get_timer_label()
        if self.indicator:
            self.indicator.set_label(label_text, "VibeBar")
        return True

    def on_menu_refresh_tick(self):
        self.update_data()
        self.build_menu()
        return True

    def build_menu(self):
        for child in self.menu.get_children():
            self.menu.remove(child)

        # 1. Заголовок текущей задачи
        task_label = f"🎯 {self.current_task_title}"
        if self.current_task_time and not self.current_is_pause:
            diff_sec = max(0, (datetime.now() - self.current_task_time).total_seconds())
            mins = int(diff_sec // 60)
            task_label += f" ({mins} мин)"

        item_cur = Gtk.MenuItem(label=task_label)
        item_cur.set_sensitive(False)
        self.menu.append(item_cur)

        self.menu.append(Gtk.SeparatorMenuItem())

        # 2. 💡 Идеи за сегодня
        if self.today_ideas:
            ideas_menu_item = Gtk.MenuItem(label=f"💡 Идеи за сегодня ({len(self.today_ideas)})")
            ideas_submenu = Gtk.Menu()
            for idea in self.today_ideas:
                it = Gtk.MenuItem(label=f"💡 {idea}")
                it.connect("activate", self.on_copy_text, idea)
                ideas_submenu.append(it)
            ideas_menu_item.set_submenu(ideas_submenu)
            self.menu.append(ideas_menu_item)

        # 3. ❗ Напоминания за сегодня
        if self.today_reminders:
            reminders_menu_item = Gtk.MenuItem(label=f"❗ Напоминания ({len(self.today_reminders)})")
            reminders_submenu = Gtk.Menu()
            for rem in self.today_reminders:
                chk_item = Gtk.CheckMenuItem(label=rem["text"])
                chk_item.set_active(rem["done"])
                chk_item.connect("toggled", self.on_toggle_reminder, rem)
                reminders_submenu.append(chk_item)
            reminders_menu_item.set_submenu(reminders_submenu)
            self.menu.append(reminders_menu_item)

        if self.today_ideas or self.today_reminders:
            self.menu.append(Gtk.SeparatorMenuItem())

        # 4. 📋 Буфер обмена (последние 15)
        clipboard_items = self.load_clipboard_history()
        clip_menu_item = Gtk.MenuItem(label=f"📋 Буфер обмена ({len(clipboard_items)})")
        clip_submenu = Gtk.Menu()

        if clipboard_items:
            for entry in clipboard_items:
                preview = entry.get("preview", entry.get("text", ""))[:45]
                it = Gtk.MenuItem(label=preview)
                it.connect("activate", self.on_paste_clipboard_entry, entry.get("text", ""))
                clip_submenu.append(it)
        else:
            empty_it = Gtk.MenuItem(label="Буфер пуст")
            empty_it.set_sensitive(False)
            clip_submenu.append(empty_it)

        clip_menu_item.set_submenu(clip_submenu)
        self.menu.append(clip_menu_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        # 5. Инструменты
        open_journal_item = Gtk.MenuItem(label="📖 Открыть журнал")
        open_journal_item.connect("activate", self.on_open_journal)
        self.menu.append(open_journal_item)

        report_item = Gtk.MenuItem(label="📊 Показать сводку")
        report_item.connect("activate", self.on_show_report)
        self.menu.append(report_item)

        pause_item = Gtk.MenuItem(label="⏸ Поставить на паузу")
        pause_item.connect("activate", self.on_set_pause)
        self.menu.append(pause_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label="🚪 Выход")
        quit_item.connect("activate", Gtk.main_quit)
        self.menu.append(quit_item)

        self.menu.show_all()

    def load_clipboard_history(self):
        if os.path.exists(self.clipboard_file):
            try:
                with open(self.clipboard_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def on_copy_text(self, widget, text):
        cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        cb.set_text(text, -1)
        cb.store()

    def on_toggle_reminder(self, widget, rem_dict):
        """Переключает статус [ ] <-> [x] в самом Markdown файле."""
        new_state = widget.get_active()
        old_raw = rem_dict["raw"]
        clean_text = rem_dict["text"]

        if new_state:
            new_raw = re.sub(r"❗\s*\[ \]", "❗ [x]", old_raw)
        else:
            new_raw = re.sub(r"❗\s*\[[xX]\]", "❗ [ ]", old_raw)

        if os.path.exists(self.journal_file):
            with open(self.journal_file, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace(old_raw, new_raw, 1)
            with open(self.journal_file, "w", encoding="utf-8") as f:
                f.write(content)
        self.update_data()

    def on_paste_clipboard_entry(self, widget, text):
        """Помещает текст в буфер и нажимает Ctrl+V через xdotool."""
        cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        cb.set_text(text, -1)
        cb.store()

        if self.autopaste:
            def do_paste():
                # Микро-задержка для возврата фокуса в активное окно
                time.sleep(0.15)
                subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+v"])
            GLib.idle_add(lambda: subprocess.Popen(["python3", "-c", f"import time, subprocess; time.sleep(0.2); subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+v'])"]))

    def on_open_journal(self, widget):
        if not os.path.exists(self.journal_file):
            os.makedirs(os.path.dirname(os.path.abspath(self.journal_file)), exist_ok=True)
            with open(self.journal_file, "w", encoding="utf-8") as f:
                f.write(f"## {datetime.now().strftime('%Y-%m-%d')}\n")
        subprocess.Popen(["xdg-open", self.journal_file])

    def on_show_report(self, widget):
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vibebar-reports.py")
        res = subprocess.run(["python3", script], stdout=subprocess.PIPE, text=True)
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Сводка VibeBar"
        )
        dialog.format_secondary_text(res.stdout)
        dialog.run()
        dialog.destroy()

    def on_set_pause(self, widget):
        add_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vibebar-add.py")
        subprocess.run(["python3", add_script, "перерыв"])
        self.update_data()
        self.on_timer_tick()

def main():
    applet = VibeBarApplet()
    Gtk.main()

if __name__ == "__main__":
    main()
