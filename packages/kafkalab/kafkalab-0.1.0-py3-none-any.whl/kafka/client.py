import json
import urllib.error
import urllib.request

from .config import get_base_url
from .errors import KafkaError
from .storage import load_credentials


class KafkaClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = get_base_url(base_url)

    def _ensure_auth(self):
        creds = load_credentials(self.base_url) or {}
        if not creds.get("token"):
            raise KafkaError("login_required")

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        creds = load_credentials(self.base_url) or {}
        token = creds.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _request(self, method: str, path: str, payload=None):
        url = f"{self.base_url}{path}"
        data = None
        headers = self._headers()
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read()
                if not body:
                    return None
                return json.loads(body.decode("utf-8"))
        except urllib.error.HTTPError as err:
            body = err.read()
            message = f"request_failed:{err.code}"
            if body:
                try:
                    data = json.loads(body.decode("utf-8"))
                    message = data.get("error", message)
                except json.JSONDecodeError:
                    pass
            raise KafkaError(message) from err

    def submit_job(self, job_type: str, payload=None):
        self._ensure_auth()
        try:
            self._ensure_capacity()
        except KafkaError as err:
            if err.code in ("no_compute_providers_available", "server_busy"):
                return self._unscheduled(job_type, err.code)
            raise
        try:
            job = self._request("POST", "/jobs", {"type": job_type, "payload": payload})
            return self._sanitize_job(job)
        except KafkaError as err:
            if err.code in ("no_providers_available", "server_busy"):
                return self._unscheduled(job_type, err.code)
            raise

    def get_job(self, job_id: str):
        self._ensure_auth()
        return self._request("GET", f"/jobs/{job_id}")

    def list_jobs(self):
        self._ensure_auth()
        return self._request("GET", "/jobs")

    def get_capacity(self):
        return self._request("GET", "/capacity")

    def _ensure_capacity(self):
        capacity = self.get_capacity()
        def _as_int(value, default=0):
            if isinstance(value, bool):
                return default
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                value = value.strip()
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        active_providers = _as_int(capacity.get("activeProviders", 0))
        busy_providers = _as_int(capacity.get("busyProviders", 0))

        if active_providers <= 0:
            raise KafkaError("no_compute_providers_available")
        if busy_providers >= active_providers:
            raise KafkaError("server_busy")

    def _unscheduled(self, job_type: str, reason: str):
        message = "job_not_scheduled"
        if reason in ("no_compute_providers_available", "no_providers_available"):
            message = "no_compute_providers_available"
        elif reason == "server_busy":
            message = "server_busy"
        return {"status": "unscheduled", "type": job_type, "error": reason, "message": message}

    def wait_for_job(self, job_id: str, poll_interval: float = 1.0, on_update=None):
        while True:
            current = self._sanitize_job(self.get_job(job_id))
            if on_update:
                try:
                    on_update(current)
                except Exception:
                    pass
            if current["status"] in ("completed", "failed", "canceled"):
                return current
            import time

            time.sleep(poll_interval)

    def _sanitize_job(self, job):
        if not isinstance(job, dict):
            return job
        sanitized = dict(job)
        sanitized.pop("providerId", None)
        sanitized.pop("ownerUserId", None)
        return sanitized
