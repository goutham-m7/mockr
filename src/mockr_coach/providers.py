"""Explicit providers: deterministic offline fixture and real JSON chat-completions."""

import json
import urllib.error
import urllib.request
from typing import Protocol
from urllib.parse import urlsplit


class Provider(Protocol):
    def complete(self, system: str, payload: dict) -> dict: ...


class ProviderError(RuntimeError):
    pass


class MockProvider:
    """Transparent smoke-test heuristic, never presented as an actual LLM judge."""

    def complete(self, system: str, payload: dict) -> dict:
        transcript = payload["transcript"]
        if payload["task"] == "probe":
            last = transcript[-1]["answer"].replace("\n", " ")[:100]
            return {"probe": f'You said “{last}”. What assumption could make that fail?'}
        criteria = []
        for criterion in payload["rubric"]:
            answer = next((t["answer"] for t in transcript if t["stage"] == criterion["stage"]), transcript[0]["answer"])
            score = min(5, 1 + len(answer.split()) // 12)
            execution = payload.get("execution")
            if criterion["id"] == "correctness" and execution:
                score = 1 + round(4 * execution["passed"] / execution["total"])
            criteria.append(dict(id=criterion["id"], score=score, quote=answer[:160], feedback="Offline heuristic: add concrete reasoning, alternatives, and measurable evidence; use a real judge for coaching quality."))
        return {"criteria": criteria}


class OpenAIProvider:
    def __init__(self, base_url: str, key: str, model: str, timeout: float = 30):
        parsed = urlsplit(base_url)
        local = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        if not key or not model or parsed.username or parsed.password or parsed.query or parsed.fragment or not parsed.hostname or (parsed.scheme != "https" and not (parsed.scheme == "http" and local)):
            raise ValueError("Set a HTTPS base URL (HTTP allowed only on loopback), API key and model")
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.key, self.model, self.timeout = key, model, timeout

    def complete(self, system: str, payload: dict) -> dict:
        body = dict(model=self.model, temperature=0, response_format={"type": "json_object"}, messages=[dict(role="system",content=system), dict(role="user",content=json.dumps(payload))])
        request = urllib.request.Request(self.url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.key}"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ValueError("Response too large")
            data = json.loads(raw)
            result = json.loads(data["choices"][0]["message"]["content"])
            if not isinstance(result, dict):
                raise ValueError("Expected JSON object")
            return result
        except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            # Never include provider response bodies, headers or credentials in errors.
            raise ProviderError("Provider request failed or returned invalid JSON; check endpoint/model configuration") from exc
