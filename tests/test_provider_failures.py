import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from mockr_coach.providers import OpenAIProvider, ProviderError


@pytest.mark.parametrize(
    "status,body",
    [
        (500, b"private provider diagnostics"),
        (200, b"not JSON"),
        (200, b'{"choices": []}'),
        (200, json.dumps({"choices": [{"message": {"content": "[]"}}]}).encode()),
        (200, b"x" * (1024 * 1024 + 1)),
    ],
)
def test_unusable_provider_responses_are_redacted(status, body):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(status)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        provider = OpenAIProvider(
            f"http://127.0.0.1:{server.server_port}/v1", "test-secret", "model"
        )
        with pytest.raises(ProviderError) as caught:
            provider.complete("system", {"task": "probe"})
        assert "test-secret" not in str(caught.value)
        assert "private provider diagnostics" not in str(caught.value)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
