"""Loopback-only UI/API. A server token and strict origin/host checks guard writes."""

import hmac
import json
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .bank import Question
from .history import History
from .providers import Provider, ProviderError
from .sandbox import SandboxUnavailable
from .session import Round


def create_server(
    db_path: Path | str,
    bank: list[Question],
    provider: Provider,
    provider_name: str,
    port: int,
) -> HTTPServer:
    questions = {q.id: q for q in bank}
    rounds: dict[str, Round] = {}
    token = secrets.token_urlsafe(32)
    assets = Path(__file__).with_name("static")

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *args):
            # Local transcripts and request paths are private, not access-log material.
            pass

        def send(self, status, data, content_type="application/json"):
            raw = (
                json.dumps(data).encode()
                if content_type == "application/json"
                else data
            )
            self.send_response(status)
            for key, value in {
                "Content-Type": content_type,
                "Content-Length": str(len(raw)),
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
                "Permissions-Policy": "microphone=(self), camera=()",
            }.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(raw)

        def allowed(self, write=False):
            hosts = {
                f"127.0.0.1:{self.server.server_port}",
                f"localhost:{self.server.server_port}",
            }
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin")
            valid = host in hosts and (origin is None or origin == "http://" + host)
            if write:
                valid = (
                    valid
                    and origin == "http://" + host
                    and hmac.compare_digest(
                        self.headers.get("X-Mockr-Token", "").encode(), token.encode()
                    )
                )
            if not valid:
                self.send(403, {"error": "Host, Origin or local server token rejected"})
            return valid

        def do_GET(self):
            if not self.allowed():
                return
            path = urlsplit(self.path)
            files = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                "/style.css": ("style.css", "text/css; charset=utf-8"),
            }
            if path.path in files:
                name, kind = files[path.path]
                self.send(200, (assets / name).read_bytes(), kind)
            elif path.path == "/api/config":
                self.send(
                    200,
                    {
                        "token": token,
                        "provider": provider_name,
                        "questions": [
                            {
                                "id": q.id,
                                "kind": q.kind,
                                "title": q.title,
                                "topic": q.topic,
                            }
                            for q in bank
                        ],
                    },
                )
            elif path.path == "/api/history":
                with History(db_path) as history:
                    self.send(200, history.summary())
            elif path.path == "/api/session":
                session_id = parse_qs(path.query).get("id", [""])[0]
                with History(db_path) as history:
                    row = history.get(session_id)
                self.send(200 if row else 404, row or {"error": "Session not found"})
            else:
                self.send(404, {"error": "Not found"})

        def do_POST(self):
            if not self.allowed(write=True):
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send(400, {"error": "Invalid Content-Length"})
                return
            if not 0 < size <= 131072:
                self.send(413, {"error": "JSON body must be 1–131072 bytes"})
                return
            if self.headers.get_content_type() != "application/json":
                self.send(415, {"error": "Expected application/json"})
                return
            try:
                payload = json.loads(self.rfile.read(size))
                if not isinstance(payload, dict):
                    raise TypeError("Expected a JSON object")
                if self.path == "/api/start":
                    question_id = payload.get("question_id")
                    if not isinstance(question_id, str) or question_id not in questions:
                        raise ValueError("Unknown question id")
                    if len(rounds) >= 8:
                        self.send(
                            409,
                            {
                                "error": "Eight rounds are already open; finish a round or restart the server"
                            },
                        )
                        return
                    interview = Round(questions[question_id], provider)
                    rounds[interview.id] = interview
                elif self.path == "/api/answer":
                    session_id = payload.get("id")
                    if not isinstance(session_id, str) or session_id not in rounds:
                        self.send(404, {"error": "Active session not found"})
                        return
                    interview = rounds[session_id]
                    interview.answer(payload.get("answer"))
                    if interview.done:
                        with History(db_path) as history:
                            history.save(interview.record(provider_name))
                        del rounds[session_id]
                else:
                    self.send(404, {"error": "Not found"})
                    return
                self.send(
                    200,
                    {
                        "id": interview.id,
                        "title": interview.question.title,
                        "kind": interview.question.kind,
                        "stage": interview.stage,
                        "prompt": interview.prompt,
                        "done": interview.done,
                        "transcript": interview.transcript,
                        "scorecard": interview.scorecard,
                        "execution": interview.execution,
                    },
                )
            except (ValueError, TypeError, UnicodeDecodeError) as exc:
                self.send(400, {"error": str(exc)})
            except SandboxUnavailable as exc:
                self.send(503, {"error": str(exc)})
            except ProviderError as exc:
                self.send(502, {"error": str(exc)})

    server = HTTPServer(("127.0.0.1", port), Handler)
    server.token = token
    return server
