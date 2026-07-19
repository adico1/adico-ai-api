"""
Cosmos addresses = SY seals (not truncated SHA).

  32 netivot (paths) · 22 otiyot · 231 gates
  uniqueness under unified SY language + geometry

Every function request:
  1) build SY seal from input (thing)
  2) request existing seal or engrave (register)
  3) seal about seal · seal about that
  4) Hebrew answer = seal faces + programming→SY map
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

from . import config, ledger, sy_address, sy_lexicon
from . import PRODUCT_ID

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


def prog_to_hebrew_words(text: str) -> str:
    sy_lexicon._load()
    rev = {}
    for e in sy_lexicon._TERMS_SORTED:
        rev.setdefault(e["to"], e["from"])
    out = text
    for prog in sorted(rev.keys(), key=len, reverse=True):
        out = out.replace(prog, rev[prog])
    return out


def resolve_request(
    *,
    user: str | None,
    op_id: str,
    params: dict,
    raw_input: str,
    machine_answer: str,
) -> dict[str, Any]:
    """SY seal cycle for one function call."""
    sy = sy_address.build_sy_address(
        raw_input=raw_input,
        op_id=op_id,
        params=params or {},
        user=user,
    )
    thing = sy["thing"]
    about = sy["about_thing"]
    about2 = sy["about_about"]
    content_hex = thing["address_hex"]

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
                "scheme": sy["scheme"],
                "address_hex": content_hex,
                "address_u64": thing["address_u64"],
                "netiv": thing["netiv"],
                "gates": thing["gates"],
                "letters": thing["letters"],
                "hebrew": thing["hebrew"],
                "about_hex": about["address_hex"],
                "about2_hex": about2["address_hex"],
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
            f"  נתיב={thing['netiv']}/32",
            f"  שערים={thing['gate_count']} (מתוך 231)",
            f"  דבר={thing['hebrew']}",
            f"  כתובת_על_כתובת={about['hebrew']}",
            f"  כתובת_על_כתובת_על_כתובת={about2['hebrew']}",
            f"  מצב={'קיים' if exists else 'נחקק_ונרשם'}",
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
        "space": "sy_32_netivot_22_otiyot_231_gates",
        "scheme": sy["scheme"],
        "geometry": sy["geometry"],
        "unified_language": "sy_words_external · programming_bind · sy_seal_address",
        "law": sy["law"],
        "thing": {
            **thing,
            "role": "unique_sy_seal_of_the_thing",
        },
        "about_thing": {
            **about,
            "role": "sy_seal_about_sy_seal",
        },
        "about_about": {
            **about2,
            "role": "sy_seal_about_seal_about_seal",
        },
        "hebrew_answer": hebrew_answer,
        "record": rec,
    }
    try:
        ledger.sign(
            "adico_cosmos_address",
            {
                "scheme": sy["scheme"],
                "mode": mode,
                "exists": exists,
                "netiv": thing["netiv"],
                "gates_n": thing["gate_count"],
                "address_hex": content_hex,
                "about_hex": about["address_hex"],
                "about2_hex": about2["address_hex"],
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
    g = cosmos.get("geometry") or {}
    return "\n".join(
        [
            "sy.address:",
            f"  scheme={cosmos.get('scheme')}",
            f"  geometry=netivot:{g.get('netivot')} otiyot:{g.get('otiyot')} gates:{g.get('gates')}",
            f"  mode={cosmos['mode']}",
            f"  exists={cosmos['exists']}",
            f"  user={cosmos['user']}",
            f"  netiv={t.get('netiv')}/32  gates={t.get('gate_count')}",
            f"  thing=0x{t['address_hex']}  he={t['hebrew']}",
            f"  about=0x{a['address_hex']}  he={a['hebrew']}",
            f"  about2=0x{a2['address_hex']}  he={a2['hebrew']}",
            f"  law={cosmos.get('law')}",
            "",
            cosmos.get("hebrew_answer") or "",
        ]
    )
