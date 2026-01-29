import http.server
import queue
import threading
import urllib.parse
import webbrowser

from .config import get_base_url
from .storage import save_credentials


def login(base_url: str | None = None, timeout: int = 180) -> dict:
    base_url = get_base_url(base_url)
    result_queue: queue.Queue[dict] = queue.Queue()

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return
            params = urllib.parse.parse_qs(parsed.query)
            token = params.get("token", [None])[0]
            user_id = params.get("user_id", [None])[0]
            if token:
                result_queue.put({"token": token, "user_id": user_id})
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Login complete. You can close this tab.")
                return
            self.send_response(400)
            self.end_headers()

        def log_message(self, format, *args):  # noqa: A002
            return

    server = http.server.HTTPServer(("localhost", 0), CallbackHandler)
    port = server.server_address[1]
    redirect_uri = f"http://localhost:{port}/callback"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    login_url = f"{base_url}/auth/portal?redirect_uri={urllib.parse.quote(redirect_uri)}"
    webbrowser.open(login_url)

    try:
        result = result_queue.get(timeout=timeout)
    finally:
        server.shutdown()
        server.server_close()

    save_credentials(base_url, result["token"], result.get("user_id"))
    return result
