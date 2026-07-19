"""
On-demand id events → system.ledger

Decider trail (every sealed id):
  1) measure_first  — does id+params already exist (cache / address table)?
  2) install        — ensure op present
  3) execute        — run op
  4) cache_hit      — re-ask one op answer

Same HMAC-32 style as Adi local bridges (loopback machine).
Disable: ADICO_LEDGER=0
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Any

from . import PRODUCT_ID, COMPANY, OWNER

# default Adi machine ledger; override with ADICO_LEDGER_PATH
DEFAULT_LEDGER = Path("/Users/adicohen/Projects/system.ledger")
# local shared used across Adi loopback services (same as azm bridge)
_DEFAULT_SHARED = b"5b4ec061f5b321e722ba1e8dcde619c1"
SHEM = "adico_ai_api"


def _enabled() -> bool:
    return os.environ.get("ADICO_LEDGER", "1") not in ("0", "false", "False")


def _path() -> Path:
    return Path(os.environ.get("ADICO_LEDGER_PATH", str(DEFAULT_LEDGER))).expanduser()


def _shared() -> bytes:
    env = os.environ.get("ADICO_LEDGER_SHARED", "")
    if env:
        return env.encode("utf-8")
    return _DEFAULT_SHARED


def sign32(b: bytes) -> str:
    return hmac.new(_shared(), b, hashlib.sha256).hexdigest()[:32]


def sign(verb: str, payload: dict[str, Any]) -> str | None:
    """Append one signed JSONL line. Returns sig or None if disabled/fail."""
    if not _enabled():
        return None
    body = {
        "ts": int(time.time()),
        "verb": verb,
        "shem": SHEM,
        "product": PRODUCT_ID,
        "company": COMPANY,
        "owner": OWNER,
        "payload": payload,
    }
    body["sig"] = sign32(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    try:
        path = _path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(body, ensure_ascii=False) + "\n")
        return body["sig"]
    except Exception:
        return None


def measure_first(op_id: str, params: dict, *, cache_hit: bool, key: str | None = None) -> str | None:
    return sign(
        "adico_measure_first",
        {
            "op_id": op_id,
            "params_digest": hashlib.sha256(
                json.dumps(params, ensure_ascii=False, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            "decision": "cache_hit_reuse" if cache_hit else "install_and_execute",
            "cache_hit": cache_hit,
            "key": key,
        },
    )


def install_event(op_id: str, install: dict) -> str | None:
    return sign("adico_on_demand_install", {"op_id": op_id, "install": install})


def execute_event(op_id: str, key: str, answer_len: int, extra: dict | None = None) -> str | None:
    payload = {"op_id": op_id, "key": key, "answer_len": answer_len}
    if extra:
        payload.update(extra)
    return sign("adico_on_demand_execute", payload)


def math_event(op_id: str, result: dict) -> str | None:
    return sign("adico_math", {"op_id": op_id, **result})


def address_sum_event(result: dict) -> str | None:
    return sign(
        "adico_address_sum",
        {
            "mode": result.get("mode"),
            "address_hex": result.get("address_hex"),
            "exists": result.get("exists"),
            "parts_n": len(result.get("parts") or []),
        },
    )
