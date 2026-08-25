# Universal Project Context & Rules: VibeBar Linux

## Overview
VibeBar Linux is an open-source voice-driven productivity companion and clipboard manager for Linux Mint (Cinnamon) and Ubuntu-based systems.

## Project Structure
- `bin/vibebar-applet.py`: Tray applet using `AyatanaAppIndicator3`.
- `bin/vibebar-record.sh`: One-touch audio recording toggle and orchestrator.
- `bin/vibebar-stt.py`: Universal STT engine (Faster-Whisper / Parakeet ONNX + Groq / OpenAI Cloud APIs).
- `bin/vibebar-add.py`: Task / Idea / Reminder / Pause classifier and Markdown journal updater.
- `bin/vibebar-clipboard.py`: Zero-CPU event-driven clipboard daemon with shell prompt filter.
- `bin/vibebar-reports.py`: Analytics and Obsidian report generator.
- `install.sh` / `uninstall.sh`: Environment setup and autostart configuration.

## Development & Test Commands
- Virtualenv: `.venv/bin/python3`
- Run Tests: `PYTHONPATH=. .venv/bin/pytest tests/`
- Start Applet: `.venv/bin/python3 bin/vibebar-applet.py`
- Start Clipboard: `.venv/bin/python3 bin/vibebar-clipboard.py`
