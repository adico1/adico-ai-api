"""
Cosmos-space unique addresses under the unified language.

Every function request:
  1) compute address id from input (thing under unified language)
  2) request exists? → reuse : register (tune)
  3) unique address about that unique address (meta)
  4) answer translated to Hebrew (22-letter external face)

From the asking user's perspective: addresses bind to user + request.
Space: full 64-bit cosmos (mod 2^64).
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any

from . import bits64, config, ledger, sy_lexicon
from . import PRODUCT_ID, OWNER

MASK64 = bits64.MASK64
_lock = threading.Lock()
_TABLE: dict[str, dict] = {}
_loaded = False


def _path() -> Path:
    return config.DATA / "cosmos_addresses.jsonl"


def _load() -> None:
    global _loaded
    if _loaded:
        return
    p = _path()
    if p.is_file():
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    k = rec.get("address_hex")
                    if k:
                        _TABLE[k] = rec
                except Exception:
                    continue
    _loaded = True


def _persist(rec: dict) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def u64_to_hebrew(u: int) -> str:
    """Map u64 → external Hebrew (base-22 otiyot only) — language answer face."""
    if u < 0:
        u = u & MASK64
    if u == 0:
        return bits64.OTIYOT_22[0]
    digits = []
    n = u
    # fixed 14 digits (max letters per limb packing capacity style)
    for _ in range(14):
        digits.append(bits64.OTIYOT_22[n % 22])
        n //= 22
        if n == 0:
            break
    return "".join(reversed(digits))


def compute_content_u64(
    *,
    user: str | None,
    op_id: str,
    params: dict,
    raw_input: str,
) -> int:
    """Unique address for the thing under unified language (user perspective)."""
    body = {
        "space": "cosmos",
        "product": PRODUCT_ID,
        "user": user or "anonymous_local",
        "op_id": op_id,
        "params": params,
        "input": raw_input,
        "language": "unified_sy_programming",
    }
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def address_of_address(content_u64: int) -> int:
    """Unique address about unique address (meta id in cosmos space)."""
    raw = b"address_about_address:" + content_u64.to_bytes(8, "big") + b":" + PRODUCT_ID.encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def address_of_address_of_address(meta_u64: int) -> int:
    """Second meta: unique address about the address-about-address."""
    raw = b"address_about_address_about:" + meta_u64.to_bytes(8, "big")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def prog_to_hebrew_words(text: str) -> str:
    """Map programming terms in a machine answer back to SY Hebrew words."""
    sy_lexicon._load()
    rev = {}
    for e in sy_lexicon._TERMS_SORTED:
        rev.setdefault(e["to"], e["from"])
    # longest programming tokens first
    out = text
    for prog in sorted(rev.keys(), key=len, reverse=True):
        he = rev[prog]
        out = out.replace(prog, he)
    return out


def resolve_request(
    *,
    user: str | None,
    op_id: str,
    params: dict,
    raw_input: str,
    machine_answer: str,
) -> dict[str, Any]:
    """
    Full cosmos address cycle for one function call.
    Returns structured dual (internal u64 + Hebrew) + existence mode.
    """
    content = compute_content_u64(
        user=user, op_id=op_id, params=params, raw_input=raw_input
    )
    about = address_of_address(content)
    about2 = address_of_address_of_address(about)

    content_hex = f"{content:016x}"
    about_hex = f"{about:016x}"
    about2_hex = f"{about2:016x}"

    content_he = u64_to_hebrew(content)
    about_he = u64_to_hebrew(about)
    about2_he = u64_to_hebrew(about2)

    with _lock:
        _load()
        if content_hex in _TABLE:
            mode = "request_existing"
            exists = True
            rec = dict(_TABLE[content_hex])
        else:
            mode = "tune_calculate_register"
            exists = False
            rec = {
                "address_hex": content_hex,
                "address_u64": content,
                "about_hex": about_hex,
                "about_u64": about,
                "about2_hex": about2_hex,
                "about2_u64": about2,
                "user": user or "anonymous_local",
                "op_id": op_id,
                "input": raw_input,
                "ts": int(time.time()),
                "mode": mode,
            }
            _TABLE[content_hex] = rec
            _persist(rec)

    hebrew_machine = prog_to_hebrew_words(machine_answer or "")
    hebrew_answer = "\n".join(
        [
            "תשובה_עברית:",
            f"  דבר={content_he}",
            f"  כתובת_על_כתובת={about_he}",
            f"  כתובת_על_כתובת_על_כתובת={about2_he}",
            f"  מצב={'קיים' if exists else 'חושב_ונרשם'}",
            f"  משתמש={user or 'מקומי'}",
            "",
            "מיפוי_תכנות_לעברית:",
            hebrew_machine if hebrew_machine.strip() else "(אין)",
        ]
    )

    out = {
        "mode": mode,
        "exists": exists,
        "user": user or "anonymous_local",
        "space": "cosmos_u64",
        "unified_language": "sy_words_external · programming_internal · u64_cosmos",
        "thing": {
            "address_u64": content,
            "address_hex": content_hex,
            "hebrew": content_he,
            "role": "unique_address_of_the_thing",
        },
        "about_thing": {
            "address_u64": about,
            "address_hex": about_hex,
            "hebrew": about_he,
            "role": "unique_address_about_unique_address",
        },
        "about_about": {
            "address_u64": about2,
            "address_hex": about2_hex,
            "hebrew": about2_he,
            "role": "unique_address_about_address_about_address",
        },
        "hebrew_answer": hebrew_answer,
        "record": rec,
    }
    try:
        ledger.sign(
            "adico_cosmos_address",
            {
                "mode": mode,
                "exists": exists,
                "address_hex": content_hex,
                "about_hex": about_hex,
                "about2_hex": about2_hex,
                "op_id": op_id,
                "user": user or "anonymous_local",
            },
        )
    except Exception:
        pass
    return out


def format_cosmos_block(cosmos: dict) -> str:
    t = cosmos["thing"]
    a = cosmos["about_thing"]
    a2 = cosmos["about_about"]
    return "\n".join(
        [
            "cosmos.address:",
            f"  mode={cosmos['mode']}",
            f"  exists={cosmos['exists']}",
            f"  user={cosmos['user']}",
            f"  thing=0x{t['address_hex']}  he={t['hebrew']}",
            f"  about=0x{a['address_hex']}  he={a['hebrew']}",
            f"  about2=0x{a2['address_hex']}  he={a2['hebrew']}",
            "",
            cosmos.get("hebrew_answer") or "",
        ]
    )
