from __future__ import annotations

import base64
from pathlib import Path


def _extract_artifacts(result: dict) -> list[dict]:
    artifacts = result.get("artifacts") or result.get("checkpoints") or []
    if not isinstance(artifacts, list):
        return []
    return [item for item in artifacts if isinstance(item, dict)]


def save_artifacts(result: dict, output_dir: str | Path) -> list[Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for artifact in _extract_artifacts(result):
        name = artifact.get("name") or artifact.get("filename")
        data = artifact.get("data")
        encoding = artifact.get("encoding", "base64")
        if not name or not data:
            continue
        if encoding == "base64":
            payload = base64.b64decode(data)
        else:
            continue
        target = output_path / name
        target.write_bytes(payload)
        saved.append(target)
    return saved
