import json
from pathlib import Path

from .artifacts import save_artifacts
from .client import KafkaClient
from .progress import ProgressTracker


def infer(
    payload,
    base_url: str | None = None,
    poll_interval: float = 1.0,
    on_update=None,
    progress: bool = True,
    log_path: str | Path | None = None,
    artifacts_dir: str | Path | None = None,
    return_raw: bool = False,
    image: str | None = None,
    command: list[str] | None = None,
    env: dict[str, str] | None = None,
    data: dict | None = None,
):
    client = KafkaClient(base_url=base_url)
    if image:
        payload = {
            "mode": "infer",
            "image": image,
            "command": command or [],
            "env": env or {},
            "data": data or {},
            "payload": payload,
        }
    job = client.submit_job("infer", payload)
    if job.get("status") == "unscheduled":
        print("infer job not scheduled:", job.get("message", job.get("error")))
        return {"status": "unscheduled", "reason": job.get("message", job.get("error"))}
    tracker = ProgressTracker(show_progress=progress)

    def _handle_update(update):
        if on_update:
            on_update(update)
        tracker.maybe_tick(update)

    result = client.wait_for_job(job["id"], poll_interval=poll_interval, on_update=_handle_update)
    tracker.close()
    if log_path:
        _write_log(log_path, result)
    if artifacts_dir:
        save_artifacts(result, artifacts_dir)
    if result.get("status") == "completed":
        summary = {"status": "completed", "result": result.get("result", {})}
    else:
        summary = {"status": result.get("status"), "error": result.get("error")}
    if return_raw:
        summary["raw"] = result
    return summary


def _write_log(path: str | Path, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2))
