from .auth import login as _login
from .inference import infer as _infer
from .remote import bundle as _bundle
from .remote import container as _container
from .remote import load as _load
from .artifacts import save_artifacts as _save_artifacts


def login(base_url: str | None = None, timeout: int = 180):
    return _login(base_url=base_url, timeout=timeout)


def infer(payload, base_url: str | None = None, poll_interval: float = 1.0):
    return _infer(payload, base_url=base_url, poll_interval=poll_interval)


def load(func, base_url: str | None = None, poll_interval: float = 1.0):
    return _load(func, base_url=base_url, poll_interval=poll_interval)


def container(
    image: str,
    command: list[str] | None = None,
    env: dict[str, str] | None = None,
    base_url: str | None = None,
    poll_interval: float = 1.0,
):
    return _container(image, command=command, env=env, base_url=base_url, poll_interval=poll_interval)


def bundle(
    archive,
    entrypoint: str,
    signing_key: str | None = None,
    base_url: str | None = None,
    poll_interval: float = 1.0,
):
    return _bundle(archive, entrypoint, signing_key=signing_key, base_url=base_url, poll_interval=poll_interval)


def save_artifacts(result, output_dir):
    return _save_artifacts(result, output_dir)
