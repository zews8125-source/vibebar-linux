#!/usr/bin/env python3
"""
vibebar-add.py
Обработка и классификация распознанного текста для VibeBar:
 - Идеи: префиксы 'идея', 'мысль', 'заметка', 'идею', 'idea' -> 💡
 - Напоминания: префиксы 'не забыть', 'напомнить', 'важно', 'запомнить', 'remind' -> ❗ [ ]
 - Паузы: 'перерыв', 'пауза', 'стоп', 'обед', 'отдых', 'pause', 'break' -> ⏸
 - Задачи: любой другой текст -> активная задача с таймером
"""

import sys
import os
import re
from datetime import datetime

def load_config():
    config = {
        "VIBEBAR_JOURNAL_FILE": os.path.expanduser("~/vibebar-journal.md")
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

def classify_text(text: str):
    """
    Классифицирует текст и возвращает (entry_type, formatted_text, payload)
    entry_type: 'idea' | 'reminder' | 'pause' | 'task'
    """
    text = text.strip()
    if not text:
        return None, "", ""

    lower = text.lower()

    # 1. Пауза / Перерыв
    pause_keywords = ["перерыв", "пауза", "стоп", "обед", "отдых", "pause", "break", "стоп таймер"]
    for kw in pause_keywords:
        if lower == kw or lower.startswith(kw + " ") or lower.startswith(kw + "."):
            return "pause", "⏸ перерыв", "перерыв"

    # 2. Напоминания (чекбоксы)
    reminder_prefixes = [
        "не забыть", "напомнить", "напомни", "важно", "запомнить",
        "remind me", "remind", "important", "todo", "купить", "сделать"
    ]
    for prefix in reminder_prefixes:
        pattern = rf"^{re.escape(prefix)}[\s:,.-]+(.*)$"
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            if not content:
                content = text
            return "reminder", f"❗ [ ] {content}", content

    # 3. Идеи
    idea_prefixes = [
        "идея", "мысль", "заметка", "идею", "idea", "note", "thought"
    ]
    for prefix in idea_prefixes:
        pattern = rf"^{re.escape(prefix)}[\s:,.-]+(.*)$"
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            if not content:
                content = text
            return "idea", f"💡 {content}", content

    # 4. Обычная задача
    return "task", text, text

def append_to_journal(entry_type: str, formatted_content: str, journal_path: str, dt: datetime = None):
    """Добавляет запись в Markdown журнал в секцию текущей даты."""
    if dt is None:
        dt = datetime.now()

    date_header = f"## {dt.strftime('%Y-%m-%d')}"
    time_str = dt.strftime("%H:%M")
    new_line = f"- {time_str} · {formatted_content}\n"

    journal_path = os.path.expanduser(journal_path)
    os.makedirs(os.path.dirname(os.path.abspath(journal_path)), exist_ok=True)

    content = ""
    if os.path.exists(journal_path):
        with open(journal_path, "r", encoding="utf-8") as f:
            content = f.read()

    lines = content.splitlines(keepends=True)
    header_idx = -1

    for i, line in enumerate(lines):
        if line.strip() == date_header:
            header_idx = i
            break

    if header_idx != -1:
        # Находим конец текущей секции даты (до следующего '## ' или до конца файла)
        insert_idx = len(lines)
        for i in range(header_idx + 1, len(lines)):
            if lines[i].startswith("## "):
                insert_idx = i
                break
        lines.insert(insert_idx, new_line)
    else:
        # Секции на сегодня еще нет -> добавляем ее в конец файла
        if lines and not lines[-1].endswith("\n"):
            lines.append("\n")
        if lines and lines[-1].strip() != "":
            lines.append("\n")
        lines.append(f"{date_header}\n")
        lines.append(new_line)

    with open(journal_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def main():
    if len(sys.argv) < 2:
        print("Использование: vibebar-add.py <распознанный текст>")
        sys.exit(1)

    raw_text = " ".join(sys.argv[1:]).strip()
    if not raw_text:
        sys.exit(0)

    config = load_config()
    journal_path = config.get("VIBEBAR_JOURNAL_FILE", "~/vibebar-journal.md")

    entry_type, formatted_text, payload = classify_text(raw_text)
    if entry_type:
        append_to_journal(entry_type, formatted_text, journal_path)
        print(f"[{entry_type.upper()}] Добавлено в {journal_path}: {formatted_text}")

if __name__ == "__main__":
    main()
