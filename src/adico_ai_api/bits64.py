"""
Representation law (Adi):

  Babylonians spoke 64-bit.
  Hebrew simplified that to 22-letter combinations (Sefer Yetzira / Book of Formations).
  We use Hebrew externally and 64-bit internally.

External speech  = limited Hebrew (22 otiyot combinations) + tool forms for machines
Internal compute = uint64 words (and limbs for longer payloads)
"""
from __future__ import annotations

import hashlib
import json
import struct
from typing import Any

# 22 Hebrew letters (Sefer Yetzira) — alef to tav, no finals as separate
OTIYOT_22 = "אבגדהוזחטיכלמנסעפצקרשת"
# finals → base
_FINALS = str.maketrans({
    "ך": "כ",
    "ם": "מ",
    "ן": "נ",
    "ף": "פ",
    "ץ": "צ",
})

MASK64 = (1 << 64) - 1
# base-22 digits fit in 64 bits: floor(64 * log(2) / log(22)) = 14 letters per word
LETTERS_PER_U64 = 14


def normalize_hebrew(text: str) -> str:
    """Keep only 22-letter stream (map finals → base). Drop niqqud / non-letters."""
    t = (text or "").translate(_FINALS)
    out = []
    for ch in t:
        if ch in OTIYOT_22:
            out.append(ch)
        # skip spaces and other — external may include spaces for humans
    return "".join(out)


def letter_index(ch: str) -> int | None:
    ch = ch.translate(_FINALS) if ch else ch
    if not ch:
        return None
    i = OTIYOT_22.find(ch)
    return i if i >= 0 else None


def hebrew_to_u64_limbs(text: str) -> list[int]:
    """
    Pack 22-letter combinations into 64-bit limbs (base-22).
    Empty → [0]. Deterministic. Internal form of external Hebrew.
    """
    stream = normalize_hebrew(text)
    if not stream:
        return [0]
    limbs: list[int] = []
    i = 0
    while i < len(stream):
        chunk = stream[i : i + LETTERS_PER_U64]
        v = 0
        for ch in chunk:
            idx = letter_index(ch)
            if idx is None:
                continue
            v = v * 22 + idx
        limbs.append(v & MASK64)
        i += LETTERS_PER_U64
    return limbs or [0]


def u64_limbs_to_hex(limbs: list[int]) -> list[str]:
    return [f"{x:016x}" for x in limbs]


def canonical_u64(op_id: str, params: dict) -> int:
    """Internal 64-bit fingerprint of a sealed op (first 8 bytes of sha256)."""
    body = json.dumps(
        {"id": op_id, "params": params},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(body).digest()[:8], "big")


def dual_rep(
    *,
    external: str,
    op_id: str | None = None,
    params: dict | None = None,
    matches: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Always expose both faces of the law:
      external: Hebrew (or tool speech string)
      internal: 64-bit limbs + op u64
    """
    limbs = hebrew_to_u64_limbs(external)
    out: dict[str, Any] = {
        "law": {
            "babylonian": "64-bit internal",
            "hebrew": "22-letter combinations external (simplified from 64-bit)",
            "use": "Hebrew externally · 64-bit internally",
        },
        "external": {
            "speech": external,
            "hebrew_stream_22": normalize_hebrew(external),
            "otiyot_count": 22,
        },
        "internal": {
            "u64_limbs": limbs,
            "u64_hex": u64_limbs_to_hex(limbs),
            "limb_count": len(limbs),
            "bits_per_limb": 64,
            "letters_per_limb_max": LETTERS_PER_U64,
            "base": 22,
        },
    }
    if op_id is not None:
        ou = canonical_u64(op_id, params or {})
        out["internal"]["op_u64"] = ou
        out["internal"]["op_u64_hex"] = f"{ou:016x}"
        out["internal"]["op_id"] = op_id
    if matches:
        # each SY term: external Hebrew term + its internal u64
        terms = []
        for m in matches:
            fr = m.get("from") or ""
            tl = hebrew_to_u64_limbs(fr)
            terms.append(
                {
                    "id": m.get("id"),
                    "external": fr,
                    "to": m.get("to"),
                    "internal_u64": tl[0] if tl else 0,
                    "internal_u64_hex": f"{(tl[0] if tl else 0):016x}",
                }
            )
        out["terms_dual"] = terms
    return out


def law_public() -> dict[str, Any]:
    return {
        "babylonian": "64-bit",
        "hebrew_simplification": "22-letter combinations (Sefer Yetzira)",
        "external": "Hebrew (limited Book of Formations lexicon)",
        "internal": "64-bit words (base-22 packed limbs + op_u64)",
        "otiyot_22": OTIYOT_22,
        "letters_per_u64": LETTERS_PER_U64,
    }
