"""OpenAI-compatible external adapter over the single Local daemon."""

from __future__ import annotations

import json
import mimetypes
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .daemon import InferenceDaemon

MAX_BODY = 1 << 20
DEFAULT_MAX_TOKENS = 8


class _RequestError(ValueError):
    """A client request field that cannot be mapped to the daemon contract."""


def _max_tokens(payload: dict[str, Any]) -> int:
    """Prefer ``max_completion_tokens`` and fall back to legacy ``max_tokens``."""
    for field in ("max_completion_tokens", "max_tokens"):
        value = payload.get(field)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise _RequestError(f"{field} must be an integer")
        return value
    return DEFAULT_MAX_TOKENS


def _content_text(content: Any) -> str:
    """Accept a string or an array of OpenAI text content parts."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        raise _RequestError("message content must be a string or an array of text parts")
    parts = []
    for part in content:
        if not isinstance(part, dict) or part.get("type") not in ("text", "input_text"):
            raise _RequestError("only text message content parts are supported")
        if not isinstance(part.get("text"), str):
            raise _RequestError("text content parts require a string text field")
        parts.append(part["text"])
    return "".join(parts)


class OpenAIAdapter:
    def __init__(self, daemon: InferenceDaemon, *, host: str = "127.0.0.1",
                 auth_token: str | None = None, static_root: str | Path | None = None):
        if host not in {"127.0.0.1", "::1", "localhost"} and not auth_token:
            raise ValueError("auth_token is required when OpenAI adapter is not loopback-only")
        self.daemon = daemon
        self.host = host
        self.auth_token = auth_token
        self.static_root = Path(static_root).resolve() if static_root else None
        self._request_id = 1000

    def _authorized(self, headers: dict[str, str]) -> bool:
        if self.auth_token is None:
            return self.host in {"127.0.0.1", "::1", "localhost"}
        supplied = headers.get("authorization", "")
        return secrets.compare_digest(supplied, f"Bearer {self.auth_token}")

    @staticmethod
    def _json(status: int, payload: dict[str, Any], *, content_type: str = "application/json"):
        return status, {"Content-Type": content_type}, json.dumps(payload, separators=(",", ":")).encode()

    def dispatch(self, method: str, path: str, headers: dict[str, str] | None = None,
                 body: bytes = b"") -> tuple[int, dict[str, str], bytes]:
        headers = {key.lower(): value for key, value in (headers or {}).items()}
        if not self._authorized(headers):
            return self._json(401, {"error": {"message": "unauthorized"}})
        if len(body) > MAX_BODY:
            return self._json(413, {"error": {"message": "request body is too large"}})
        if method == "OPTIONS":
            return 204, {}, b""
        if method == "GET" and self.static_root is not None and path in {"/", "/qwen38.html"}:
            page = (self.static_root / "qwen38.html").resolve()
            if page.parent == self.static_root and page.is_file():
                return self._json(200, {}, content_type="text/html; charset=utf-8")[:2] + (page.read_bytes(),)
        if method == "GET" and path == "/health":
            status = self.daemon.handle({"method": "status"})[0][1]
            ready = bool(status.get("handles")) and status.get("state") != "stopped"
            return self._json(200 if ready else 503, {"status": "ready" if ready else "degraded",
                                                        "effect_authority": "none"})
        if method == "GET" and path == "/v1/models":
            handles = self.daemon.handle({"method": "status"})[0][1].get("handles", [])
            return self._json(200, {"object": "list", "data": [
                {"id": item["model_id"], "object": "model", "owned_by": "simplicio-local"}
                for item in handles
            ]})
        if method != "POST" or path not in {"/v1/completions", "/v1/chat/completions"}:
            if path == "/v1/embeddings":
                return self._json(501, {"error": {"message": "embeddings capability is not enabled"}})
            return self._json(404, {"error": {"message": "unknown route"}})
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._json(400, {"error": {"message": "malformed JSON"}})
        if not isinstance(payload, dict):
            return self._json(400, {"error": {"message": "request must be an object"}})
        if "tools" in payload or payload.get("tool_choice") not in (None, "none"):
            return self._json(400, {"error": {"message": "tool execution is forbidden in Local"}})
        if payload.get("n", 1) != 1 or payload.get("logprobs") not in (None, False):
            return self._json(400, {"error": {"message": "unsupported sampling field"}})
        handles = self.daemon.handle({"method": "status"})[0][1].get("handles", [])
        if not handles:
            return self._json(503, {"error": {"message": "no model is loaded"}})
        active = handles[0]
        prompt = payload.get("prompt", "")
        if path == "/v1/chat/completions":
            messages = payload.get("messages", [])
            if not isinstance(messages, list) or not messages:
                return self._json(400, {"error": {"message": "messages is required"}})
            try:
                prompt = _content_text(messages[-1].get("content")) if isinstance(messages[-1], dict) else ""
            except _RequestError as exc:
                return self._json(400, {"error": {"message": str(exc)}})
        try:
            max_tokens = _max_tokens(payload)
        except _RequestError as exc:
            return self._json(400, {"error": {"message": str(exc)}})
        self._request_id += 1
        request = {"method": "generate", "handle_id": active["handle_id"],
                   "backend": str(payload.get("backend", active.get("backend", "fixture"))),
                   "prompt": str(prompt),
                   "max_tokens": max_tokens,
                   "profile": str(payload.get("profile", "resident"))}
        events = self.daemon.handle(request, self._request_id)
        terminal = events[-1][1]
        if not terminal.get("ok", False):
            return self._json(409, {"error": terminal.get("error", {"message": "generation failed"}),
                                    "receipt": terminal.get("receipt")})
        request_id = f"chatcmpl-simplicio-{self._request_id}"
        text = terminal.get("text", "")
        receipt = terminal.get("receipt") or {}
        metrics = receipt.get("metrics") or {}
        prompt_tokens = int((metrics.get("tokens.prompt") or {}).get("value") or 0)
        completion_tokens = int((metrics.get("tokens.generated") or {}).get("value") or
                                terminal.get("generated_tokens", 0))
        if payload.get("stream"):
            chunks = []
            for event_kind, event in events:
                if event_kind == 3:
                    chunks.append("data: " + json.dumps({"id": request_id, "object": "chat.completion.chunk",
                                                          "choices": [{"index": 0, "delta": {"content": event["text"]},
                                                                       "finish_reason": None}]}) + "\n\n")
            chunks.append("data: [DONE]\n\n")
            return 200, {"Content-Type": "text/event-stream", "Cache-Control": "no-cache"}, "".join(chunks).encode()
        response = {"id": request_id, "object": "chat.completion" if "chat" in path else "text_completion",
                    "model": active.get("model_id", terminal.get("handle_id", "fixture")),
                    "choices": [{"index": 0, "text": text, "message": {"role": "assistant", "content": text},
                                 "finish_reason": terminal.get("stop_reason", "length")}],
                    "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
                              "total_tokens": prompt_tokens + completion_tokens},
                    "metadata": {"requested_backend": terminal.get("requested_backend"),
                                 "effective_backend": terminal.get("effective_backend"),
                                 "receipt": receipt}}
        return self._json(200, response)


def run_server(daemon: InferenceDaemon, *, host: str = "127.0.0.1", port: int = 8080,
               auth_token: str | None = None, static_root: str | Path | None = None) -> None:
    adapter = OpenAIAdapter(daemon, host=host, auth_token=auth_token, static_root=static_root)

    class Handler(BaseHTTPRequestHandler):
        def _dispatch(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b""
            status, headers, payload = adapter.dispatch(self.command, self.path, dict(self.headers), body)
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if payload:
                self.wfile.write(payload)

        do_GET = _dispatch
        do_POST = _dispatch
        do_OPTIONS = _dispatch

        def log_message(self, *_: object) -> None:
            return

    ThreadingHTTPServer((host, port), Handler).serve_forever()
