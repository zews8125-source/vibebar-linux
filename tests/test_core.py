import os
import json
import tempfile
import pytest
from datetime import datetime, timedelta

from bin import (
    vibebar_add as v_add,
    vibebar_reports as v_reports,
    vibebar_clipboard as v_clipboard
)

def test_classifier_idea():
    etype, formatted, payload = v_add.classify_text("Идея: сделать интеграцию с Telegram ботом")
    assert etype == "idea"
    assert formatted == "💡 сделать интеграцию с Telegram ботом"
    assert payload == "сделать интеграцию с Telegram ботом"

def test_classifier_reminder():
    etype, formatted, payload = v_add.classify_text("Не забыть купить кофе и молоко")
    assert etype == "reminder"
    assert formatted == "❗ [ ] купить кофе и молоко"

def test_classifier_pause():
    etype, formatted, payload = v_add.classify_text("перерыв")
    assert etype == "pause"
    assert "⏸" in formatted

def test_classifier_task():
    etype, formatted, payload = v_add.classify_text("Программирование модуля STT для VibeBar")
    assert etype == "task"
    assert formatted == "Программирование модуля STT для VibeBar"

def test_journal_append_and_parse():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".md") as tmp:
        tmp_path = tmp.name

    try:
        now = datetime.now()
        v_add.append_to_journal("task", "Тестовая задача 1", tmp_path, now)
        v_add.append_to_journal("idea", "💡 Крутая мысль", tmp_path, now)
        v_add.append_to_journal("reminder", "❗ [ ] Проверить почту", tmp_path, now)
        v_add.append_to_journal("pause", "⏸ перерыв", tmp_path, now)

        days = v_reports.parse_journal(tmp_path)
        date_str = now.strftime("%Y-%m-%d")
        assert date_str in days
        entries = days[date_str]
        assert len(entries) == 4
        assert entries[0]["type"] == "task"
        assert entries[1]["type"] == "idea"
        assert entries[2]["type"] == "reminder"
        assert entries[3]["type"] == "pause"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_clipboard_clean_prompt():
    raw_terminal = "[user@linuxmint:~/projects]$ ls -la\ntotal 24"
    monitor = v_clipboard.ClipboardMonitor.__new__(v_clipboard.ClipboardMonitor)
    monitor.clean_terminal = True
    monitor.prompt_re = r"^(\[\w+@\w+[^\]]*\]|\w+@[\w\.-]+:.*?)[$#]\s*"
    cleaned = monitor.clean_text(raw_terminal)
    assert "ls -la" in cleaned
    assert "[user@linuxmint" not in cleaned
