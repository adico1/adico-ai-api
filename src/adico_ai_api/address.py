"""
sum = address op (programming only)

  sum is a request of an address that already exists,
  or a tuning request to calculate the address.

Parts may be:
  · SY words (mapped to their internal u64)
  · explicit u64 (0x… or decimal)
  · programming terms that alias a known SY word target (input, output, process, …)

Result address = (sum of part u64s) mod 2^64
"""
from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any

from . import bits64, config, sy_lexicon

MASK64 = bits64.MASK64
_lock = threading.Lock()
# address_hex → record
_TABLE: dict[str, dict] = {}
_loaded = False


def _table_path() -> Path:
    return config.DATA / "addresses.jsonl"


def _load_table() -> None:
    global _loaded
    if _loaded:
        return
    path = _table_path()
    if path.is_file():
        with path.open("r", encoding="utf-8") as f:
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
    path = _table_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _term_u64(term: str) -> int:
    limbs = bits64.external_to_u64_limbs(term)
    return limbs[0] if limbs else 0


def _prog_to_sy() -> dict[str, dict]:
    """programming_term -> first lexicon entry."""
    sy_lexicon._load()
    out: dict[str, dict] = {}
    for e in sy_lexicon._TERMS_SORTED:
        to = e.get("to")
        if to and to not in out:
            out[to] = e
    return out


def resolve_part(token: str) -> dict[str, Any]:
    """Resolve one sum operand to a u64 address component."""
    t = (token or "").strip()
    if not t:
        raise ValueError("empty part")

    # explicit hex address
    if re.fullmatch(r"0x[0-9a-fA-F]+", t):
        v = int(t, 16) & MASK64
        return {"kind": "u64_hex", "token": t, "u64": v, "u64_hex": f"{v:016x}"}
    if re.fullmatch(r"[0-9a-fA-F]{16}", t):
        v = int(t, 16) & MASK64
        return {"kind": "u64_hex", "token": t, "u64": v, "u64_hex": f"{v:016x}"}

    # plain integer (tuning weight / numeric address)
    if re.fullmatch(r"[+-]?\d+", t):
        v = int(t) & MASK64
        return {"kind": "u64_int", "token": t, "u64": v, "u64_hex": f"{v:016x}"}

    # programming term alias (input, output, process, …)
    prog = _prog_to_sy()
    if t in prog:
        e = prog[t]
        v = _term_u64(e["from"])
        return {
            "kind": "programming_term",
            "token": t,
            "sy_word": e["from"],
            "sy_id": e["id"],
            "u64": v,
            "u64_hex": f"{v:016x}",
        }

    # SY word (with optional ו)
    raw = t
    if t.startswith("ו") and len(t) > 1:
        t = t[1:]
    matches = sy_lexicon.match_terms(t)
    # exact full-token SY match preferred
    for m in matches:
        if m["from"] == t or m.get("surface") == raw:
            v = _term_u64(m["from"])
            return {
                "kind": "sy_word",
                "token": raw,
                "sy_word": m["from"],
                "sy_id": m["id"],
                "programming": m["to"],
                "u64": v,
                "u64_hex": f"{v:016x}",
            }
    # single known lexicon term exact
    sy_lexicon._load()
    for e in sy_lexicon._TERMS_SORTED:
        if e["from"] == t:
            v = _term_u64(e["from"])
            return {
                "kind": "sy_word",
                "token": raw,
                "sy_word": e["from"],
                "sy_id": e["id"],
                "programming": e["to"],
                "u64": v,
                "u64_hex": f"{v:016x}",
            }

    raise ValueError(f"unknown_address_part:{token}")


def parse_sum_payload(raw: str) -> dict[str, Any]:
    """
    Parse sum operands from:
      sum 1 2 3 | sum(a,b) | sum מים אש | sum input output | sum 0x.. 0x..
    """
    s = (raw or "").strip()
    s = s.replace(",", " ").replace("+", " ")
    # keep SY multi-word terms: longest lexicon terms first via match on full string
    # Strategy: try to peel longest SY terms, else whitespace tokens
    parts: list[dict] = []
    rest = s
    sy_lexicon._load()
    terms = sorted([e["from"] for e in sy_lexicon._TERMS_SORTED], key=len, reverse=True)

    while rest.strip():
        rest = rest.lstrip()
        matched = False
        # ו + term
        for term in terms:
            for form in (term, "ו" + term if not term.startswith("ו") else term):
                if rest.startswith(form) and (
                    len(rest) == len(form) or rest[len(form)].isspace() or rest[len(form)] in ",+"
                ):
                    parts.append(resolve_part(form))
                    rest = rest[len(form) :]
                    matched = True
                    break
            if matched:
                break
        if matched:
            continue
        # next whitespace token
        m = re.match(r"(\S+)", rest)
        if not m:
            break
        tok = m.group(1)
        parts.append(resolve_part(tok))
        rest = rest[len(tok) :]

    if not parts:
        raise ValueError("empty_sum")
    return {"parts": parts}


def sum_address(parts: list[dict]) -> dict[str, Any]:
    """
    Sum part u64s → address.
    If address already in table → request_existing.
    Else → tune_calculate (register).
    """
    with _lock:
        _load_table()
        total = 0
        for p in parts:
            total = (total + int(p["u64"])) & MASK64
        addr_hex = f"{total:016x}"
        if addr_hex in _TABLE:
            rec = dict(_TABLE[addr_hex])
            return {
                "mode": "request_existing",
                "address": total,
                "address_hex": addr_hex,
                "address_u64": total,
                "parts": parts,
                "exists": True,
                "record": rec,
            }
        rec = {
            "address": total,
            "address_hex": addr_hex,
            "parts": parts,
            "mode": "tune_calculate",
        }
        _TABLE[addr_hex] = rec
        _persist(rec)
        return {
            "mode": "tune_calculate",
            "address": total,
            "address_hex": addr_hex,
            "address_u64": total,
            "parts": parts,
            "exists": False,
            "record": rec,
        }


def format_sum_result(result: dict) -> str:
    mode = result["mode"]
    lines = [
        "address.sum:",
        f"  mode={mode}",
        f"  address=0x{result['address_hex']}",
        f"  address_u64={result['address_u64']}",
        f"  exists={result['exists']}",
        "  parts:",
    ]
    for p in result.get("parts") or []:
        bit = f"0x{p['u64_hex']}"
        if p.get("kind") == "sy_word":
            lines.append(
                f"    + {p.get('sy_word')} ({p.get('programming')}) {bit}"
            )
        elif p.get("kind") == "programming_term":
            lines.append(
                f"    + {p.get('token')} <- {p.get('sy_word')} {bit}"
            )
        else:
            lines.append(f"    + {p.get('token')} {bit}")
    if mode == "request_existing":
        lines.append("  note=address already registered — request of existing address")
    else:
        lines.append("  note=tuning request — address calculated and registered")
    lines.append("  law=sum is address request or address calculate (tune)")
    return "\n".join(lines)
