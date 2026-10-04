import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
DATA = ROOT / ".data"
DATA.mkdir(exist_ok=True)
EXPORT_DIR = ROOT / "exports"
EXPORT_DIR.mkdir(exist_ok=True)

PRESETS = {
    "OpenAI": "https://api.openai.com/v1",
    "Anthropic": "https://api.anthropic.com/v1",
    "Google Gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "OpenRouter": "https://openrouter.ai/api/v1",
    "Groq": "https://api.groq.com/openai/v1",
    "Custom (OpenAI-compatible)": "",
}

DEFAULTS = {
    "theme": "Light",
    "provider": "Ollama",
    "ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
    "ollama_model": "",
    "cloud_provider": "OpenAI",
    "cloud_base_url": os.getenv("LLM_BASE_URL", ""),
    "cloud_model": "",
    "depth": "Standard",
    "max_sources_standard": 10,
    "max_sources_deep": 20,
    "llm_timeout": 120,
    "search_timeout": 20,
    "min_score": 25,
    "prefer_scholarly": True,
    "require_corroboration": True,
    "strict_quote_check": True,
    "export_format": "PDF",
    "export_map": True,
    "export_evidence": True,
    "export_log": False,
}

_FILE = DATA / "settings.json"


def env_api_key():
    return os.getenv("LLM_API_KEY", "")


def contact_email():
    return os.getenv("CONTACT_EMAIL", "")


def load_settings():
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads(_FILE.read_text(encoding="utf-8")))
    except Exception:
        pass
    return cfg


def save_settings(cfg):
    try:
        _FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception:
        pass
