"""Local one-op store: same (id, params) → same answer forever (until cache file removed)."""
from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from typing import Any

_lock = threading.Lock()
_mem: dict[str, dict] = {}
_loaded_for: Path | None = None


def canonical_key(op_id: str, params: dict) -> str:
    body = {"id": op_id, "params": params}
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _load(path: Path) -> None:
    global _loaded_for
    if _loaded_for == path and _mem:
        return
    _mem.clear()
    if path.is_file():
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    k = rec.get("key")
                    if k:
                        _mem[k] = rec
                except Exception:
                    continue
    _loaded_for = path


def get(path: Path, op_id: str, params: dict) -> dict | None:
    key = canonical_key(op_id, params)
    with _lock:
        _load(path)
        rec = _mem.get(key)
        if rec is None:
            return None
        return dict(rec)


def put(path: Path, op_id: str, params: dict, answer: str, answer_that_answers: dict) -> dict:
    key = canonical_key(op_id, params)
    rec = {
        "key": key,
        "id": op_id,
        "params": params,
        "answer": answer,
        "answer_that_answers": answer_that_answers,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        _load(path)
        _mem[key] = rec
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def stats(path: Path) -> dict[str, Any]:
    with _lock:
        _load(path)
        return {"path": str(path), "entries": len(_mem)}
