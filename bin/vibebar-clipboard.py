#!/usr/bin/env python3
"""
vibebar-clipboard.py
Фоновый демон мониторинга буфера обмена для VibeBar:
 - Использует события Gtk.Clipboard (zero CPU polling)
 - Сохраняет последние N записей в JSON
 - Очищает терминальные приглашения (prompts) при необходимости
"""

import sys
import os
import json
import re
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

def load_config():
    config = {
        "VIBEBAR_CLIPBOARD_FILE": os.path.expanduser("~/vibebar-clipboard.json"),
        "VIBEBAR_BUFFER_MAX": 15,
        "VIBEBAR_CLEAN_TERMINAL": 1,
        "VIBEBAR_PROMPT_RE": r"^(\[\w+@\w+[^\]]*\]|\w+@[\w\.-]+:.*?)[$#]\s*"
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
                if k == "VIBEBAR_BUFFER_MAX":
                    config[k] = int(v)
                elif k == "VIBEBAR_CLEAN_TERMINAL":
                    config[k] = int(v)
                else:
                    v = os.path.expandvars(os.path.expanduser(v))
                    config[k] = v
    return config

class ClipboardMonitor:
    def __init__(self):
        self.config = load_config()
        self.history_file = os.path.expanduser(self.config.get("VIBEBAR_CLIPBOARD_FILE", "~/vibebar-clipboard.json"))
        self.max_items = int(self.config.get("VIBEBAR_BUFFER_MAX", 15))
        self.clean_terminal = bool(int(self.config.get("VIBEBAR_CLEAN_TERMINAL", 1)))
        self.prompt_re = self.config.get("VIBEBAR_PROMPT_RE", r"^(\[\w+@\w+[^\]]*\]|\w+@[\w\.-]+:.*?)[$#]\s*")
        
        self.history = self.load_history()
        self.last_text = self.history[0]["text"] if self.history else ""

        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.clipboard.connect("owner-change", self.on_owner_change)

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception:
                pass
        return []

    def save_history(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.history_file)), exist_ok=True)
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history[:self.max_items], f, ensure_ascii=False, indent=2)

    def clean_text(self, text: str) -> str:
        if not self.clean_terminal:
            return text
        lines = text.splitlines()
        cleaned_lines = []
        pattern = re.compile(self.prompt_re)
        for line in lines:
            cleaned_lines.append(pattern.sub("", line))
        return "\n".join(cleaned_lines)

    def on_owner_change(self, clipboard, event):
        # Асинхронно запрашиваем текст
        clipboard.request_text(self.on_text_received)

    def on_text_received(self, clipboard, text, data=None):
        if not text:
            return
        
        text = text.strip()
        if not text or text == self.last_text:
            return

        cleaned = self.clean_text(text)
        self.last_text = text

        # Удаляем дубликаты
        self.history = [item for item in self.history if item.get("text") != text and item.get("text") != cleaned]

        # Добавляем в начало
        preview = cleaned if len(cleaned) <= 60 else cleaned[:57] + "..."
        entry = {
            "text": cleaned,
            "raw": text,
            "preview": preview.replace("\n", " ")
        }
        self.history.insert(0, entry)
        self.save_history()

def main():
    monitor = ClipboardMonitor()
    Gtk.main()

if __name__ == "__main__":
    main()
