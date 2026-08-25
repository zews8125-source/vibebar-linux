#!/usr/bin/env python3
"""
vibebar-stt.py
Универсальный STT движок для VibeBar:
 1. Local: Faster-Whisper / Parakeet ONNX / NeMo (локально, оптимизировано для CPU/старых ПК)
 2. Groq: Ультрабыстрый облачный Whisper Turbo API
 3. OpenAI: Whisper-1 API
 4. Custom: Любой совместимый OpenAI audio transcription API
"""

import sys
import os
import io
import time
import json
import requests

def load_config():
    config = {
        "STT_PROVIDER": "local",
        "STT_LOCAL_MODEL": "base",
        "STT_LANGUAGE": "ru",
        "GROQ_API_KEY": "",
        "OPENAI_API_KEY": "",
        "CUSTOM_STT_URL": "http://localhost:8000/v1/audio/transcriptions",
        "CUSTOM_STT_API_KEY": "",
        "CUSTOM_STT_MODEL": "whisper-1",
        "WHISPER_DIR": os.path.expanduser("~/.local/share/whisper.cpp")
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
                v = v.strip()
                # Удаляем inline комментарии если есть
                if "#" in v and not (v.startswith('"') and v.endswith('"')) and not (v.startswith("'") and v.endswith("'")):
                    v = v.split("#", 1)[0].strip()
                v = v.strip('"\'')
                v = os.path.expandvars(os.path.expanduser(v))
                config[k] = v
    return config

def transcribe_local(audio_path: str, model_name: str = "base", language: str = "ru") -> str:
    """Локальная транскрибация через faster-whisper с квантованием int8 для максимальной скорости на CPU."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        # Fallback на whisper.cpp если faster-whisper еще не подтянут
        return transcribe_whisper_cpp(audio_path, model_name)

    # Используем int8 вычисления для старых и слабых CPU без AVX512
    compute_type = "int8"
    try:
        model = WhisperModel(model_name, device="cpu", compute_type=compute_type)
        lang_arg = None if language == "auto" else language
        segments, info = model.transcribe(
            audio_path,
            language=lang_arg,
            beam_size=3,
            vad_filter=True, # отсечение тишины
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        text = " ".join([seg.text for seg in segments]).strip()
        return text
    except Exception as e:
        sys.stderr.write(f"Ошибка faster-whisper: {e}\n")
        # Попробуем whisper.cpp fallback
        return transcribe_whisper_cpp(audio_path, model_name)

def transcribe_whisper_cpp(audio_path: str, model_name: str = "base") -> str:
    """Fallback транскрибация через скомпилированный бинарник whisper.cpp"""
    import subprocess
    whisper_dir = os.path.expanduser("~/.local/share/whisper.cpp")
    binary = os.path.join(whisper_dir, "main")
    model_file = os.path.join(whisper_dir, "models", f"ggml-{model_name}.bin")

    if not os.path.exists(binary) or not os.path.exists(model_file):
        raise RuntimeError("Локальный движок STT не настроен (ни faster-whisper, ни whisper.cpp).")

    txt_out = audio_path + ".txt"
    cmd = [binary, "-m", model_file, "-f", audio_path, "-otxt", "-l", "auto", "-nt"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if os.path.exists(txt_out):
        with open(txt_out, "r", encoding="utf-8") as f:
            text = f.read().strip()
        try:
            os.remove(txt_out)
        except OSError:
            pass
        return text
    return res.stdout.strip()

def transcribe_groq(audio_path: str, api_key: str, language: str = "ru") -> str:
    """Транскрибация через Groq Cloud Whisper API (скорость 200-300x realtime)."""
    if not api_key:
        raise ValueError("GROQ_API_KEY не указан в config.env")

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
        data = {
            "model": "whisper-large-v3-turbo",
            "response_format": "json"
        }
        if language and language != "auto":
            data["language"] = language

        resp = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        resp.raise_for_status()
        res_json = resp.json()
        return res_json.get("text", "").strip()

def transcribe_openai(audio_path: str, api_key: str, language: str = "ru") -> str:
    """Транскрибация через официальный OpenAI Whisper API."""
    if not api_key:
        raise ValueError("OPENAI_API_KEY не указан в config.env")

    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
        data = {
            "model": "whisper-1",
            "response_format": "json"
        }
        if language and language != "auto":
            data["language"] = language

        resp = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        resp.raise_for_status()
        res_json = resp.json()
        return res_json.get("text", "").strip()

def transcribe_custom(audio_path: str, url: str, api_key: str = "", model: str = "whisper-1", language: str = "ru") -> str:
    """Транскрибация через пользовательский OpenAI-совместимый API сервер."""
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
        data = {
            "model": model or "whisper-1",
            "response_format": "json"
        }
        if language and language != "auto":
            data["language"] = language

        resp = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        resp.raise_for_status()
        res_json = resp.json()
        return res_json.get("text", "").strip()

def main():
    if len(sys.argv) < 2:
        print("Использование: vibebar-stt.py <путь_к_аудио.wav>")
        sys.exit(1)

    audio_file = sys.argv[1]
    if not os.path.exists(audio_file):
        sys.stderr.write(f"Аудиофайл не найден: {audio_file}\n")
        sys.exit(1)

    config = load_config()
    provider = config.get("STT_PROVIDER", "local").lower().strip()
    language = config.get("STT_LANGUAGE", "ru").strip()
    local_model = config.get("STT_LOCAL_MODEL", "base").strip()

    text = ""
    try:
        if provider == "groq":
            text = transcribe_groq(audio_file, config.get("GROQ_API_KEY", ""), language)
        elif provider == "openai":
            text = transcribe_openai(audio_file, config.get("OPENAI_API_KEY", ""), language)
        elif provider == "custom":
            text = transcribe_custom(
                audio_file,
                config.get("CUSTOM_STT_URL", ""),
                config.get("CUSTOM_STT_API_KEY", ""),
                config.get("CUSTOM_STT_MODEL", "whisper-1"),
                language
            )
        else:
            # По умолчанию local (Faster-Whisper / Parakeet)
            text = transcribe_local(audio_file, local_model, language)
    except Exception as e:
        sys.stderr.write(f"Ошибка провайдера '{provider}': {e}. Переключаюсь на локальный режим...\n")
        try:
            text = transcribe_local(audio_file, local_model, language)
        except Exception as err2:
            sys.stderr.write(f"Критическая ошибка распознавания: {err2}\n")
            sys.exit(1)

    print(text.strip())

if __name__ == "__main__":
    main()
