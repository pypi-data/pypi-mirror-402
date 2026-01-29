import base64
from pathlib import Path

from .client import KafkaClient
from .errors import KafkaError


def _coerce_path(value: str | Path) -> Path:
    return value if isinstance(value, Path) else Path(value)


def _extract_output(result: dict, failure_code: str):
    if result.get("status") != "completed":
        raise KafkaError(failure_code, f"status={result.get('status')}")
    output = result.get("result", result)
    if isinstance(output, dict) and "output" in output:
        return output["output"]
    if isinstance(output, dict) and output.get("error"):
        raise KafkaError("remote_execution_error", str(output.get("error")))
    return output


class RemoteFunction:
    def __init__(self, wasm_bytes: bytes, base_url: str | None = None, poll_interval: float = 1.0) -> None:
        self._client = KafkaClient(base_url=base_url)
        self._poll_interval = poll_interval
        self._payload = base64.b64encode(wasm_bytes).decode("ascii")

    def __call__(self, *args, **kwargs):
        job = self._client.submit_job(
            "function",
            {
                "encoding": "wasm/base64",
                "module": self._payload,
                "args": args,
                "kwargs": kwargs,
            },
        )
        if job.get("status") == "unscheduled":
            return job
        result = self._client.wait_for_job(job["id"], poll_interval=self._poll_interval)
        return _extract_output(result, "remote_function_failed")


class RemoteContainer:
    def __init__(
        self,
        image: str,
        command: list[str] | None = None,
        env: dict[str, str] | None = None,
        base_url: str | None = None,
        poll_interval: float = 1.0,
    ) -> None:
        self._client = KafkaClient(base_url=base_url)
        self._poll_interval = poll_interval
        self._image = image
        self._command = command or []
        self._env = env or {}

    def __call__(self, *args, **kwargs):
        job = self._client.submit_job(
            "container",
            {
                "image": self._image,
                "command": self._command,
                "env": self._env,
                "args": args,
                "kwargs": kwargs,
            },
        )
        if job.get("status") == "unscheduled":
            return job
        result = self._client.wait_for_job(job["id"], poll_interval=self._poll_interval)
        return _extract_output(result, "remote_container_failed")


class RemoteBundle:
    def __init__(
        self,
        archive_bytes: bytes,
        entrypoint: str,
        signature: str | None = None,
        base_url: str | None = None,
        poll_interval: float = 1.0,
    ) -> None:
        self._client = KafkaClient(base_url=base_url)
        self._poll_interval = poll_interval
        self._entrypoint = entrypoint
        self._archive = base64.b64encode(archive_bytes).decode("ascii")
        self._signature = signature

    def __call__(self, *args, **kwargs):
        payload = {
            "archive": self._archive,
            "entrypoint": self._entrypoint,
            "args": args,
            "kwargs": kwargs,
        }
        if self._signature:
            payload["signature"] = self._signature
        job = self._client.submit_job("bundle", payload)
        if job.get("status") == "unscheduled":
            return job
        result = self._client.wait_for_job(job["id"], poll_interval=self._poll_interval)
        return _extract_output(result, "remote_bundle_failed")


def load(func, base_url: str | None = None, poll_interval: float = 1.0) -> RemoteFunction:
    if isinstance(func, (str, Path)):
        wasm_path = _coerce_path(func)
        if not wasm_path.exists():
            raise KafkaError("wasm_module_not_found", str(wasm_path))
        wasm_bytes = wasm_path.read_bytes()
        return RemoteFunction(wasm_bytes, base_url=base_url, poll_interval=poll_interval)
    if isinstance(func, (bytes, bytearray)):
        return RemoteFunction(bytes(func), base_url=base_url, poll_interval=poll_interval)
    raise KafkaError("python_functions_not_supported_use_wasm")


def container(
    image: str,
    command: list[str] | None = None,
    env: dict[str, str] | None = None,
    base_url: str | None = None,
    poll_interval: float = 1.0,
) -> RemoteContainer:
    return RemoteContainer(image, command=command, env=env, base_url=base_url, poll_interval=poll_interval)


def bundle(
    archive: str | Path | bytes | bytearray,
    entrypoint: str,
    signing_key: str | None = None,
    base_url: str | None = None,
    poll_interval: float = 1.0,
) -> RemoteBundle:
    if isinstance(archive, (str, Path)):
        bundle_path = _coerce_path(archive)
        if not bundle_path.exists():
            raise KafkaError("bundle_not_found", str(bundle_path))
        archive_bytes = bundle_path.read_bytes()
    elif isinstance(archive, (bytes, bytearray)):
        archive_bytes = bytes(archive)
    else:
        raise KafkaError("bundle_invalid_archive")
    signature = None
    if signing_key:
        signature = _sign_bundle(archive_bytes, signing_key)
    return RemoteBundle(
        archive_bytes,
        entrypoint=entrypoint,
        signature=signature,
        base_url=base_url,
        poll_interval=poll_interval,
    )


def _sign_bundle(archive_bytes: bytes, signing_key: str) -> str:
    import hashlib
    import hmac

    digest = hmac.new(signing_key.encode("utf-8"), archive_bytes, hashlib.sha256).hexdigest()
    return digest
