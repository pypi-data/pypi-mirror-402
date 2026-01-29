import json
from pathlib import Path

from .artifacts import save_artifacts
from .client import KafkaClient
from .progress import ProgressTracker


class KafkaTrainer:
    def __init__(self, dataloader, model, optimizer, objective_function, base_url: str | None = None) -> None:
        self.dataloader = dataloader
        self.model = model
        self.optimizer = optimizer
        self.objective_function = objective_function
        self.client = KafkaClient(base_url=base_url)

    def train(
        self,
        show_tensorboard: bool = False,
        poll_interval: float = 1.0,
        epochs: int | None = None,
        on_batch=None,
        on_update=None,
        metrics_fn=None,
        show_progress: bool = True,
        log_path: str | Path | None = None,
        artifacts_dir: str | Path | None = None,
        return_raw: bool = False,
        image: str | None = None,
        command: list[str] | None = None,
        env: dict[str, str] | None = None,
        data: dict | None = None,
        checkpoints: bool = False,
    ):
        if epochs is None:
            epochs = 1
        if epochs <= 0:
            raise ValueError("epochs must be >= 1")
        total_steps = None
        if hasattr(self.dataloader, "__len__"):
            try:
                total_steps = len(self.dataloader) * epochs
            except Exception:
                total_steps = None
        payload = {
            "mode": "train",
            "show_tensorboard": show_tensorboard,
            "epochs": epochs,
            "metadata": {
                "dataloader": str(self.dataloader),
                "model": str(self.model),
            },
        }
        if image:
            payload["image"] = image
            payload["command"] = command or []
            payload["env"] = env or {}
            payload["data"] = data or {}
            payload["checkpoints"] = checkpoints
        if total_steps:
            payload["steps_per_epoch"] = max(1, total_steps // epochs)
        schema = _state_schema(self.model)
        if schema:
            payload["state_schema"] = schema
        if on_batch:
            payload["stream_progress"] = True
        if metrics_fn:
            payload["metrics"] = getattr(metrics_fn, "__name__", "custom")
        job = self.client.submit_job("train", payload)
        if job.get("status") == "unscheduled":
            print("train job not scheduled:", job.get("message", job.get("error")))
            return {"status": "unscheduled", "reason": job.get("message", job.get("error"))}
        job_id = job["id"]

        progress = ProgressTracker(total_steps, show_progress=show_progress)

        def _handle_update(update):
            if on_update:
                on_update(update)
            progress.maybe_tick(update)
            if on_batch:
                progress_payload = update.get("progress")
                if isinstance(progress_payload, dict) and progress_payload.get("batch"):
                    on_batch(progress_payload)

        result = self.client.wait_for_job(job_id, poll_interval=poll_interval, on_update=_handle_update)
        progress.close()
        if log_path:
            _write_log(log_path, result)

        if artifacts_dir:
            save_artifacts(result, artifacts_dir)
        if isinstance(result.get("result"), dict) and result["result"].get("state_dict"):
            _apply_state_dict(self.model, result["result"]["state_dict"])
        _apply_safetensors(self.model, result.get("result"))
        summary = {"status": result.get("status"), "job_id": job_id}
        if result.get("status") == "completed":
            summary["result"] = result.get("result", {})
            if metrics_fn:
                try:
                    summary["metrics"] = metrics_fn(summary["result"])
                except Exception:
                    summary["metrics"] = None
        else:
            summary["error"] = result.get("error")
        if return_raw:
            summary["raw"] = result
        return summary


def _write_log(path: str | Path, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2))


def _apply_state_dict(model, state_dict: dict) -> None:
    try:
        import torch
    except Exception:
        return
    if not hasattr(model, "state_dict") or not hasattr(model, "load_state_dict"):
        return
    current = model.state_dict()
    next_state = {}
    for key, value in state_dict.items():
        if key not in current:
            continue
        try:
            next_state[key] = torch.tensor(value, dtype=current[key].dtype).reshape(current[key].shape)
        except Exception:
            next_state[key] = current[key]
    try:
        model.load_state_dict(next_state, strict=False)
    except Exception:
        return


def _apply_safetensors(model, result: dict | None) -> None:
    if not isinstance(result, dict):
        return
    artifacts = result.get("artifacts")
    if not isinstance(artifacts, list):
        return
    entry = next((item for item in artifacts if item.get("name") == "model.safetensors"), None)
    if not entry or entry.get("encoding") != "base64":
        return
    data = entry.get("data")
    if not data:
        return
    try:
        import base64
        from safetensors.torch import load as load_safetensors
    except Exception:
        return
    try:
        raw = base64.b64decode(data)
        state = load_safetensors(raw)
        model.load_state_dict(state, strict=False)
    except Exception:
        return


def _state_schema(model) -> list[dict]:
    try:
        import torch
    except Exception:
        return []
    if not hasattr(model, "state_dict"):
        return []
    schema = []
    for name, tensor in model.state_dict().items():
        if not isinstance(tensor, torch.Tensor):
            continue
        schema.append(
            {
                "name": name,
                "shape": list(tensor.shape),
                "dtype": str(tensor.dtype),
            }
        )
    return schema
