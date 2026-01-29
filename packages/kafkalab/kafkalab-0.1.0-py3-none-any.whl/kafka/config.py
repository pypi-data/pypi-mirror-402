import os


def get_base_url(base_url: str | None) -> str:
    if base_url is None:
        base_url = os.getenv("KAFKA_SERVER_URL", "http://localhost:4000")
    return base_url.rstrip("/")
