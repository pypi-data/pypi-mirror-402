"""
Пути к данным приложения. Работает при установке через pip:
- JOB_STALKER_DATA или платформенная user data dir.
- Обратная совместимость: если в cwd есть папка data/ — используем её (legacy).
"""
import os
from pathlib import Path


def _default_user_data_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return Path(base) / "JobStalker"
    if os.environ.get("XDG_DATA_HOME"):
        return Path(os.environ["XDG_DATA_HOME"]) / "job-stalker"
    # Linux и прочие
    return Path.home() / ".local" / "share" / "job-stalker"


def get_data_dir() -> Path:
    """
    Директория для credentials, session, settings, БД и т.п.
    - JOB_STALKER_DATA — переопределение
    - иначе: ./data если существует (legacy), иначе user data dir
    """
    explicit = os.environ.get("JOB_STALKER_DATA", "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()

    cwd_data = Path("data").resolve()
    if cwd_data.exists():
        return cwd_data

    d = _default_user_data_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d
