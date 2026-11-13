import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from mockr_coach.providers import OpenAIProvider, ProviderError


def test_redirect_cannot_forward_api_key():
    captured = []

    class Sink(BaseHTTPRequestHandler):
        def do_GET(self):
            captured.append(self.headers.get("Authorization"))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{}")

        def log_message(self, *args):
            pass

    sink = HTTPServer(("127.0.0.1", 0), Sink)

    class Redirect(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{sink.server_port}/steal")
            self.end_headers()

        def log_message(self, *args):
            pass

    redirect = HTTPServer(("127.0.0.1", 0), Redirect)
    threads = [
        threading.Thread(target=s.serve_forever, daemon=True) for s in (sink, redirect)
    ]
    for thread in threads:
        thread.start()
    try:
        with pytest.raises(ProviderError):
            OpenAIProvider(
                f"http://127.0.0.1:{redirect.server_port}/v1", "test-secret", "model"
            ).complete("system", {})
        assert captured == []
    finally:
        for server in (sink, redirect):
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join()
