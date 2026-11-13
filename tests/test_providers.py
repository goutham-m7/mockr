import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from mockr_coach.providers import OpenAIProvider, ProviderError


@pytest.fixture
def endpoint():
    captured = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            captured.append((self.path, self.headers['Authorization'],json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(dict(choices=[dict(message=dict(content=json.dumps(dict(probe='Why?'))))])).encode())
        def log_message(self, *args): pass
    server = HTTPServer(('127.0.0.1',0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}/v1', captured
    server.shutdown(); server.server_close(); thread.join()


def test_openai_http_contract(endpoint):
    url, captured = endpoint
    assert OpenAIProvider(url, 'test-key', 'test-model').complete('System',dict(task='probe')) == dict(probe='Why?')
    path, auth, body = captured[0]
    assert path == '/v1/chat/completions'
    assert auth == 'Bearer test-key'
    assert body['model'] == 'test-model'
    assert body['response_format'] == dict(type='json_object')
    assert json.loads(body['messages'][1]['content']) == dict(task='probe')


@pytest.mark.parametrize('url,key,model', [('https://example.com','', 'm'),('ftp://bad','k','m'),('https://u:p@example.com','k','m'),('http://example.com','k','m'),('https://example.com','k','')])
def test_invalid_provider_configuration(url,key,model):
    with pytest.raises(ValueError): OpenAIProvider(url,key,model)


def test_network_error_is_redacted():
    with pytest.raises(ProviderError, match='request failed') as exc:
        OpenAIProvider('http://127.0.0.1:1/v1','secret','model', timeout=.1).complete('s',{})
    assert 'secret' not in str(exc.value)
