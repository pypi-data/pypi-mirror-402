from __future__ import annotations


class ProgressTracker:
    def __init__(self, total_steps: int | None = None, show_progress: bool = True) -> None:
        self._show = show_progress
        self._total = total_steps
        self._bar = None
        self._current = 0
        if show_progress and total_steps:
            self._bar = _get_tqdm()(total=total_steps)

    def maybe_tick(self, update: dict) -> None:
        progress = update.get("progress")
        if not isinstance(progress, dict):
            return
        if not self._bar and self._show:
            total = progress.get("total")
            if isinstance(total, int) and total > 0:
                self._bar = _get_tqdm()(total=total)
        if not self._bar:
            return
        step = progress.get("step")
        if isinstance(step, int):
            delta = max(0, step - self._current)
            if delta:
                self._bar.update(delta)
                self._current = step
        metrics = progress.get("metrics")
        loss = progress.get("loss")
        accuracy = progress.get("accuracy")
        val_loss = progress.get("val_loss")
        if isinstance(metrics, dict):
            loss = metrics.get("loss", loss)
            accuracy = metrics.get("accuracy", accuracy)
            val_loss = metrics.get("val_loss", val_loss)
        postfix = {}
        if isinstance(loss, (int, float)):
            postfix["loss"] = round(float(loss), 4)
        if isinstance(accuracy, (int, float)):
            postfix["acc"] = round(float(accuracy), 4)
        if isinstance(val_loss, (int, float)):
            postfix["val_loss"] = round(float(val_loss), 4)
        if postfix and hasattr(self._bar, "set_postfix"):
            self._bar.set_postfix(postfix)

    def close(self) -> None:
        if self._bar:
            self._bar.close()


def _get_tqdm():
    try:
        from tqdm import tqdm

        return tqdm
    except Exception:
        def _noop(*_args, **_kwargs):
            class _Bar:
                def update(self, *_a, **_k):
                    return None

                def close(self):
                    return None

                def set_postfix(self, *_a, **_k):
                    return None

            return _Bar()

        return _noop
