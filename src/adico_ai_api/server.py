#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Industry HTTP face — OpenAI / Ollama / Anthropic-shaped. Local data. Loopback default."""
from __future__ import annotations

import json
import sys
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

# allow `python3 -m adico_ai_api.server` from repo root without install
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from adico_ai_api import COMPANY, OWNER, PRODUCT_ID, PRODUCT_NAME, __version__  # noqa: E402
from adico_ai_api import cache, catalog, config, pipeline  # noqa: E402


def _extract_user_text(body: dict, path: str) -> str:
    if path.startswith("/api/generate"):
        return str(body.get("prompt") or "")
    if "messages" in body and isinstance(body["messages"], list):
        for m in reversed(body["messages"]):
            if isinstance(m, dict) and m.get("role") == "user":
                c = m.get("content")
                if isinstance(c, str):
                    return c
                return json.dumps(c, ensure_ascii=False)
        return ""
    return str(body.get("message") or body.get("text") or body.get("prompt") or "")


def _extract_batch(body: dict) -> list[str]:
    """Optional parallel: {\"texts\":[...]} or multiple user messages all run in parallel."""
    if isinstance(body.get("texts"), list):
        return [str(t) for t in body["texts"]]
    msgs = body.get("messages")
    if isinstance(msgs, list) and body.get("adico_parallel") is True:
        out = []
        for m in msgs:
            if isinstance(m, dict) and m.get("role") == "user":
                c = m.get("content")
                out.append(c if isinstance(c, str) else json.dumps(c, ensure_ascii=False))
        return out
    return []


class H(BaseHTTPRequestHandler):
    server_version = f"adico-ai-api/{__version__}"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _client_ok(self) -> bool:
        return self.client_address[0] in ("127.0.0.1", "::1", "localhost")

    def _send(self, code: int, obj: dict, content_type: str = "application/json; charset=utf-8"):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Adico-Product", PRODUCT_ID)
        self.send_header("X-Adico-Local-Data", "1")
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-api-key")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if not self._client_ok():
            return self._send(403, {"error": "loopback only"})
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path in ("/", "/health", "/v1/health"):
            return self._send(
                200,
                {
                    "ok": True,
                    "product": PRODUCT_ID,
                    "name": PRODUCT_NAME,
                    "company": COMPANY,
                    "owner": OWNER,
                    "version": __version__,
                    "bind": f"{config.HOST}:{config.PORT}",
                    "data": str(config.DATA),
                    "cache": cache.stats(config.CACHE_PATH),
                    "ops": catalog.list_ops(),
                    "law": {
                        "data": "local",
                        "life": "network (this repo + multi-dev)",
                        "deterministic": "id→install→execute→dual→cache once",
                        "max_request": "everything (via learned speech + catalog growth)",
                        "multilingual": False,
                        "mysticism": False,
                        "speech": "sy_words_only",
                        "target": "programming_terms_only",
                        "internal": "64-bit",
                        "talk": "GET /v1/talk — SY words only",
                        "decider": "measure_first | install_and_execute → system.ledger",
                        "math": ["sum(address)", "add", "sub", "mul", "div", "mod", "pow"],
                        "industry_today": "practically nothing complete",
                        "potential": "everything in parallel",
                    },
                    "endpoints": {
                        "GET /health": "status",
                        "GET /v1/talk": "how to speak sealed forms (required learning)",
                        "GET /v1/models": "OpenAI models list",
                        "GET /api/tags": "Ollama tags",
                        "POST /v1/chat/completions": "OpenAI chat (content = sealed speech)",
                        "POST /v1/messages": "Anthropic-shaped",
                        "POST /api/chat": "Ollama chat",
                        "POST /api/generate": "Ollama generate",
                        "POST /v1/ops/batch": "parallel texts[]",
                    },
                },
            )
        if path in ("/v1/talk", "/talk"):
            return self._send(200, catalog.talk_protocol())
        if path in ("/v1/models",):
            return self._send(
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": PRODUCT_ID,
                            "object": "model",
                            "created": 1720000000,
                            "owned_by": COMPANY,
                        },
                        {
                            "id": "adico-ops-parallel",
                            "object": "model",
                            "created": 1720000000,
                            "owned_by": COMPANY,
                        },
                    ],
                },
            )
        if path.startswith("/api/tags"):
            return self._send(
                200,
                {
                    "models": [
                        {
                            "name": f"{PRODUCT_ID}:latest",
                            "model": f"{PRODUCT_ID}:latest",
                            "modified_at": "2026-07-19T00:00:00Z",
                            "size": 1,
                            "digest": PRODUCT_ID,
                            "details": {"family": "deterministic-ops"},
                        }
                    ]
                },
            )
        if path.startswith("/api/version"):
            return self._send(200, {"version": f"adico-ai-api-{__version__}"})
        return self._send(404, {"error": "not found", "path": path})

    def do_POST(self):
        if not self._client_ok():
            return self._send(403, {"error": "loopback only"})
        path = urlparse(self.path).path.rstrip("/") or "/"
        body = self._read_json()
        try:
            if path in ("/v1/ops/batch",):
                texts = body.get("texts") or []
                if not texts:
                    return self._send(400, {"error": "texts required"})
                results = pipeline.run_many([str(t) for t in texts])
                return self._send(200, {"ok": True, "n": len(results), "results": results})

            is_messages = path.startswith("/v1/messages")
            is_chat = (
                path.startswith("/v1/chat/completions")
                or path.startswith("/api/chat")
                or path.startswith("/api/generate")
                or is_messages
            )
            if not is_chat:
                return self._send(404, {"error": "not found", "path": path})

            batch = _extract_batch(body)
            if batch:
                results = pipeline.run_many(batch)
                # industry single content = joined; full dual in adico
                content = "\n---\n".join(pipeline.format_user_visible(r) for r in results)
                adi = {"parallel": True, "results": results}
            else:
                text = _extract_user_text(body, path)
                if not str(text).strip():
                    return self._send(400, {"error": "empty message"})
                result = pipeline.run_one(text)
                content = pipeline.format_user_visible(result)
                adi = result

            mid = f"{PRODUCT_ID}-{int(time.time() * 1000)}"
            if is_messages:
                return self._send(
                    200,
                    {
                        "id": "msg_" + mid,
                        "type": "message",
                        "role": "assistant",
                        "model": PRODUCT_ID,
                        "content": [{"type": "text", "text": content}],
                        "stop_reason": "end_turn",
                        "usage": {"input_tokens": 0, "output_tokens": len(content)},
                        "adico": adi,
                    },
                )
            if path.startswith("/api/generate"):
                return self._send(
                    200,
                    {
                        "model": PRODUCT_ID,
                        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "response": content,
                        "done": True,
                        "adico": adi,
                    },
                )
            # OpenAI + Ollama /api/chat
            if path.startswith("/api/chat"):
                return self._send(
                    200,
                    {
                        "model": PRODUCT_ID,
                        "message": {"role": "assistant", "content": content},
                        "done": True,
                        "adico": adi,
                    },
                )
            return self._send(
                200,
                {
                    "id": mid,
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": body.get("model") or PRODUCT_ID,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": content},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": len(content),
                        "total_tokens": len(content),
                    },
                    "adico": adi,
                },
            )
        except Exception as e:
            return self._send(
                500,
                {"error": str(e), "trace": traceback.format_exc()[-800:]},
            )


def main():
    if not config.ALLOW_NON_LOOPBACK and config.HOST not in ("127.0.0.1", "localhost", "::1"):
        raise SystemExit("loopback only — set ADICO_ALLOW_NON_LOOPBACK=1 to override")
    config.DATA.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer((config.HOST, config.PORT), H)
    httpd.allow_reuse_address = True
    print(f"[adico-ai-api] {PRODUCT_NAME} http://{config.HOST}:{config.PORT}")
    print(f"[adico-ai-api] data={config.DATA} · ops={catalog.list_ops()}")
    print("[adico-ai-api] GET /health · POST /v1/chat/completions · POST /v1/ops/batch")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[adico-ai-api] stop")


if __name__ == "__main__":
    main()
