import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".kafka"
TOKEN_PATH = CONFIG_DIR / "credentials.json"


def _load_all() -> dict:
    if not TOKEN_PATH.exists():
        return {}
    with TOKEN_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_credentials(base_url: str) -> dict | None:
    data = _load_all()
    return data.get(base_url)


def save_credentials(base_url: str, token: str, user_id: str | None = None) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = _load_all()
    data[base_url] = {"token": token, "user_id": user_id}
    with TOKEN_PATH.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
