# Project State: VibeBar Linux (Margulan's concept port)

## Current Status: COMPLETED & VERIFIED
- Target OS: Linux Mint 22.3 (Zena) / Ubuntu 24.04 LTS (Noble) with AyatanaAppIndicator3.
- Key modules implemented:
  - `bin/vibebar-stt.py`: Universal STT layer (Local int8 Whisper/Parakeet + Cloud APIs Groq/OpenAI/Custom).
  - `bin/vibebar-applet.py`: Dynamic Tray Applet with live timer and interactive menus.
  - `bin/vibebar-record.sh`: Toggle audio recorder with notifications.
  - `bin/vibebar-add.py`: Text classifier (Tasks, Ideas, Reminders with interactive checkboxes, Pauses).
  - `bin/vibebar-clipboard.py`: Event-driven clipboard monitor with prompt filter.
  - `bin/vibebar-reports.py`: Time tracking analytics and Obsidian markdown export.
  - `install.sh` & `uninstall.sh`: Automated installer and autostart configurator.
  - `original_sources/`: Preserved reference repositories (macrowhisper, swiftbar).
  - Unit tests in `tests/test_core.py` passing (6/6).
