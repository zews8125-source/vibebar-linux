#!/usr/bin/env python3
"""
vibebar-reports.py
Генератор аналитики и отчетов распределения времени:
 - Подсчет времени активных задач за день и неделю
 - Исключение пауз и отсечение ночных незавершенных задач
 - Формирование отчета Markdown для вывода или экспорта в Obsidian Vault
"""

import sys
import os
import re
from datetime import datetime, timedelta

def load_config():
    config = {
        "VIBEBAR_JOURNAL_FILE": os.path.expanduser("~/vibebar-journal.md"),
        "VIBEBAR_OBSIDIAN_VAULT_FILE": ""
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

def parse_journal(journal_path: str):
    """Парсит Markdown журнал и возвращает структуру по датам:
    {
      'YYYY-MM-DD': [
         {'time': 'HH:MM', 'type': 'task'|'idea'|'reminder'|'pause', 'text': str, 'done': bool}
      ]
    }
    """
    journal_path = os.path.expanduser(journal_path)
    if not os.path.exists(journal_path):
        return {}

    days = {}
    current_date = None

    line_pattern = re.compile(r"^-\s*(\d{1,2}:\d{2})\s*·\s*(.*)$")

    with open(journal_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str.startswith("## "):
                # Заголовок даты: ## YYYY-MM-DD
                current_date = line_str[3:].strip()
                days[current_date] = []
                continue

            if not current_date:
                continue

            match = line_pattern.match(line_str)
            if match:
                time_str = match.group(1)
                content = match.group(2).strip()

                if content.startswith("💡"):
                    days[current_date].append({
                        "time": time_str,
                        "type": "idea",
                        "text": content[2:].strip(),
                        "raw": line_str
                    })
                elif content.startswith("❗"):
                    # Чекбокс напоминания: ❗ [ ] Текст или ❗ [x] Текст
                    done = "[x]" in content or "[X]" in content
                    clean_text = re.sub(r"^❗\s*\[[ xX]\]\s*", "", content)
                    days[current_date].append({
                        "time": time_str,
                        "type": "reminder",
                        "text": clean_text,
                        "done": done,
                        "raw": line_str
                    })
                elif content.startswith("⏸"):
                    days[current_date].append({
                        "time": time_str,
                        "type": "pause",
                        "text": "Перерыв",
                        "raw": line_str
                    })
                else:
                    days[current_date].append({
                        "time": time_str,
                        "type": "task",
                        "text": content,
                        "raw": line_str
                    })

    return days

def calculate_day_report(date_str: str, entries: list, now_dt: datetime = None):
    """
    Рассчитывает продолжительность задач для одного дня.
    """
    if now_dt is None:
        now_dt = datetime.now()

    today_str = now_dt.strftime("%Y-%m-%d")
    is_today = (date_str == today_str)

    task_durations = {}
    ideas = []
    reminders = []

    # Отфильтровываем только timeline события (задачи и паузы)
    timeline = []
    for e in entries:
        if e["type"] == "idea":
            ideas.append(e["text"])
        elif e["type"] == "reminder":
            reminders.append(e)
        elif e["type"] in ("task", "pause"):
            try:
                t_obj = datetime.strptime(f"{date_str} {e['time']}", "%Y-%m-%d %H:%M")
                timeline.append((t_obj, e["type"], e["text"]))
            except ValueError:
                pass

    timeline.sort(key=lambda x: x[0])

    total_work_seconds = 0

    for i in range(len(timeline)):
        start_time, item_type, title = timeline[i]
        
        # Определение времени окончания
        if i + 1 < len(timeline):
            end_time = timeline[i + 1][0]
        else:
            if is_today:
                end_time = max(start_time, now_dt)
            else:
                # Прошедший день без завершения -> не считаем до бесконечности
                continue

        duration_sec = (end_time - start_time).total_seconds()
        if duration_sec <= 0:
            continue

        if item_type == "task":
            task_durations[title] = task_durations.get(title, 0) + duration_sec
            total_work_seconds += duration_sec

    return {
        "date": date_str,
        "tasks": task_durations,
        "total_seconds": total_work_seconds,
        "ideas": ideas,
        "reminders": reminders
    }

def format_duration(seconds: float) -> str:
    mins = int(seconds // 60)
    hours = mins // 60
    rem_mins = mins % 60
    if hours > 0:
        return f"{hours}ч {rem_mins:02d}м"
    return f"{rem_mins}м"

def generate_markdown_report(day_report: dict) -> str:
    lines = []
    date_str = day_report["date"]
    total_str = format_duration(day_report["total_seconds"])

    lines.append(f"# 📊 Сводка VibeBar за {date_str}")
    lines.append(f"**Общее продуктивное время:** `{total_str}`\n")

    lines.append("## ⏱ Задачи и время")
    if day_report["tasks"]:
        for task, sec in sorted(day_report["tasks"].items(), key=lambda x: x[1], reverse=True):
            percent = (sec / day_report["total_seconds"] * 100) if day_report["total_seconds"] > 0 else 0
            lines.append(f"- **{task}**: `{format_duration(sec)}` ({percent:.1f}%)")
    else:
        lines.append("_Нет зафиксированных задач_")

    if day_report["ideas"]:
        lines.append("\n## 💡 Идеи за день")
        for idea in day_report["ideas"]:
            lines.append(f"- {idea}")

    if day_report["reminders"]:
        lines.append("\n## ❗ Напоминания")
        for rem in day_report["reminders"]:
            chk = "[x]" if rem.get("done") else "[ ]"
            lines.append(f"- {chk} {rem['text']}")

    lines.append("\n---\n_Сгенерировано VibeBar Linux_")
    return "\n".join(lines)

def main():
    config = load_config()
    journal_path = config.get("VIBEBAR_JOURNAL_FILE", "~/vibebar-journal.md")
    obsidian_file = config.get("VIBEBAR_OBSIDIAN_VAULT_FILE", "")

    parsed_days = parse_journal(journal_path)
    today_str = datetime.now().strftime("%Y-%m-%d")

    target_date = sys.argv[1] if len(sys.argv) > 1 else today_str
    entries = parsed_days.get(target_date, [])

    report_data = calculate_day_report(target_date, entries)
    md_output = generate_markdown_report(report_data)

    print(md_output)

    # Экспорт в Obsidian если указан файл
    if obsidian_file:
        obsidian_path = os.path.expanduser(obsidian_file)
        try:
            os.makedirs(os.path.dirname(os.path.abspath(obsidian_path)), exist_ok=True)
            with open(obsidian_path, "w", encoding="utf-8") as f:
                f.write(md_output)
            print(f"\n[OK] Сводка успешно экспортирована в Obsidian: {obsidian_path}")
        except Exception as e:
            print(f"\n[Ошибка] Не удалось записать в Obsidian: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
