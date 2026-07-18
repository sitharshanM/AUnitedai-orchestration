import json
import os

CONFIG_FILE = "worker_config.json"

DEFAULT_CONFIG = {
    "research": {
        "backend": "Gemini",
        "model": "gemini-2.5-flash-lite",
        "temperature": 0.1,
        "custom_prompt": ""
    },
    "writing": {
        "backend": "Groq",
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.7,
        "custom_prompt": ""
    },
    "analysis": {
        "backend": "Ollama",
        "model": "qwen2.5",
        "temperature": 0.0,
        "custom_prompt": ""
    },
    "coding": {
        "backend": "Ollama",
        "model": "devstral:latest",
        "temperature": 0.0,
        "custom_prompt": ""
    },
    "review": {
        "backend": "Ollama",
        "model": "llama3.1",
        "temperature": 0.3,
        "custom_prompt": ""
    },
    "file_writer": {
        "backend": "Ollama",
        "model": "qwen2.5-coder:7b",
        "temperature": 0.0,
        "custom_prompt": ""
    },
    "security_audit": {
        "backend": "Gemini",
        "model": "gemini-2.5-flash-lite",
        "temperature": 0.0,
        "custom_prompt": ""
    },
    "orchestrator": {
        "backend": "Gemini",
        "model": "gemini-2.5-flash-lite",
        "temperature": 0.0,
        "custom_prompt": ""
    },
    "critic": {
        "backend": "Gemini",
        "model": "gemini-2.5-flash-lite",
        "temperature": 0.0,
        "custom_prompt": ""
    },
    "synthesizer": {
        "backend": "Gemini",
        "model": "gemini-2.5-flash-lite",
        "temperature": 0.3,
        "custom_prompt": ""
    }
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Merge with defaults to ensure all keys exist
            merged = DEFAULT_CONFIG.copy()
            for k, v in config.items():
                if k in merged:
                    merged[k].update(v)
            return merged
    except Exception:
        return DEFAULT_CONFIG

def save_config(config_data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)
