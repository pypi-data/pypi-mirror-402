import json
import os
from pathlib import Path

from dotenv import load_dotenv

from .paths import get_data_dir

# 1) .env в текущей директории (dev / обратная совместимость)
load_dotenv()
# 2) .env в директории данных (удобно при установке через pip)
_data_dir = get_data_dir()
_dotenv_in_data = _data_dir / ".env"
if _dotenv_in_data.exists():
    load_dotenv(_dotenv_in_data)

_credentials_cache = None
CREDENTIALS_FILE = _data_dir / "credentials.json"


def _get_credentials_raw() -> dict:
    if not CREDENTIALS_FILE.exists():
        return {}
    try:
        with open(CREDENTIALS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def reload_credentials():
    """Перечитать credentials.json (после сохранения через веб)."""
    global _credentials_cache
    _credentials_cache = None


def _get(key: str, env_key: str, default, *, to_int: bool = False):
    raw = os.getenv(env_key)
    if raw is not None and str(raw).strip() != "":
        v = str(raw).strip()
        return int(v) if to_int else v

    global _credentials_cache
    if _credentials_cache is None:
        _credentials_cache = _get_credentials_raw()
    raw = _credentials_cache.get(key)
    if raw is not None and str(raw).strip() != "":
        v = str(raw).strip()
        return int(v) if to_int else v
    return default


def _csv(env_name):
    v = os.getenv(env_name, "").strip()
    return [x.strip() for x in v.split(",") if x.strip()]


def get_api_id() -> int:
    return _get("api_id", "API_ID", 0, to_int=True)


def get_api_hash() -> str:
    return _get("api_hash", "API_HASH", "")


def get_session_name() -> str:
    return _get("session_name", "SESSION_NAME", "filter_session")


def get_dest_chat_id():
    return _get("dest_chat_id", "DEST_CHAT_ID", None)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or ""
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or ""
KEYWORDS = _csv("KEYWORDS")
BLACKLIST = _csv("BLACKLIST")
REGEXES = _csv("REGEXES")
ALLOW_MEDIA = set(_csv("ALLOW_MEDIA") or ["text", "photo", "video", "document"])
CHANNELS = _csv("CHANNELS")
FORWARD_MODE = os.getenv("FORWARD_MODE", "copy")


def validate_config():
    if not get_api_id() or not get_api_hash():
        raise RuntimeError("API_ID and API_HASH must be set. Enter them in the auth screen or in credentials.")
    if not get_dest_chat_id():
        raise RuntimeError("DEST_CHAT_ID must be set. Enter it in the auth screen, settings or credentials.")


def has_credentials() -> bool:
    """Есть ли минимум для авторизации Pyrogram: API_ID и API_HASH."""
    return bool(get_api_id() and get_api_hash())


def save_credentials(*, api_id: int, api_hash: str, dest_chat_id: str = None, session_name: str = None):
    """Сохранить credentials в data_dir/credentials.json и перезагрузить кэш."""
    data = {}
    if CREDENTIALS_FILE.exists():
        try:
            with open(CREDENTIALS_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    if api_id is not None:
        data["api_id"] = int(api_id)
    if api_hash is not None:
        data["api_hash"] = str(api_hash).strip()
    if dest_chat_id is not None:
        data["dest_chat_id"] = str(dest_chat_id).strip() or None
    if session_name is not None:
        data["session_name"] = str(session_name).strip() or "filter_session"
    _data_dir.mkdir(parents=True, exist_ok=True)
    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    reload_credentials()
