"""
Representation law (Adi):

  Babylonians spoke 64-bit.
  Hebrew simplified that to 22-letter combinations (Sefer Yetzira / Book of Formations).
  We use Hebrew externally and 64-bit internally.

External speech  = 22 otiyot + empty spaces + punctuation
Internal compute = uint64 words (base-N packed limbs + op_u64)
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any

# 22 Hebrew letters (Sefer Yetzira) — alef to tav
OTIYOT_22 = "אבגדהוזחטיכלמנסעפצקרשת"
# finals → base letter
_FINALS = str.maketrans({
    "ך": "כ",
    "ם": "מ",
    "ן": "נ",
    "ף": "פ",
    "ץ": "צ",
})

# empty spaces (kept in external stream + internal pack)
SPACES = " \t\n\r\u00a0"  # space, tab, LF, CR, NBSP

# punctuation (Latin + Hebrew marks + common symbols)
PUNCT = (
    ".,;:!?…·•"
    "'\"“”‘’׳״"
    "-–—־"
    "()[]{}"
    "/\\|"
    "@#$%^&*_+=<>~`"
    "«»‹›"
)

# Full external alphabet: 22 letters + spaces + punctuation (fixed order = deterministic base)
ALPHABET = OTIYOT_22 + SPACES + PUNCT
BASE = len(ALPHABET)
_INDEX = {ch: i for i, ch in enumerate(ALPHABET)}

MASK64 = (1 << 64) - 1
# max symbols per 64-bit limb in this base
CHARS_PER_U64 = max(1, int(math.floor(64 * math.log(2) / math.log(BASE))))


def normalize_external(text: str) -> str:
    """
    External stream for packing:
      · map Hebrew finals → base 22
      · keep 22 letters, empty spaces, punctuation
      · drop niqqud and anything outside the alphabet
    """
    t = (text or "").translate(_FINALS)
    out: list[str] = []
    for ch in t:
        if ch in _INDEX:
            out.append(ch)
    return "".join(out)


def normalize_hebrew(text: str) -> str:
    """Letters-only 22-stream (no spaces/punct). Kept for SY letter face."""
    t = (text or "").translate(_FINALS)
    return "".join(ch for ch in t if ch in OTIYOT_22)


def char_index(ch: str) -> int | None:
    if not ch:
        return None
    ch = ch.translate(_FINALS)
    return _INDEX.get(ch)


def letter_index(ch: str) -> int | None:
    """Index in 22 otiyot only (0..21), or None."""
    ch = ch.translate(_FINALS) if ch else ch
    if not ch:
        return None
    i = OTIYOT_22.find(ch)
    return i if i >= 0 else None


def external_to_u64_limbs(text: str) -> list[int]:
    """
    Pack external stream (22 letters + spaces + punct) into 64-bit limbs.
    Empty stream → [0]. Deterministic.
    """
    stream = normalize_external(text)
    if not stream:
        return [0]
    limbs: list[int] = []
    i = 0
    n = CHARS_PER_U64
    while i < len(stream):
        chunk = stream[i : i + n]
        v = 0
        for ch in chunk:
            idx = char_index(ch)
            if idx is None:
                continue
            v = v * BASE + idx
        limbs.append(v & MASK64)
        i += n
    return limbs or [0]


def hebrew_to_u64_limbs(text: str) -> list[int]:
    """Alias: full external pack (letters + spaces + punct)."""
    return external_to_u64_limbs(text)


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
      external: Hebrew + spaces + punctuation
      internal: 64-bit limbs + op u64
    """
    stream = normalize_external(external)
    letters = normalize_hebrew(external)
    limbs = external_to_u64_limbs(external)
    out: dict[str, Any] = {
        "law": {
            "babylonian": "64-bit internal",
            "hebrew": "22-letter combinations external (simplified from 64-bit)",
            "spaces_punct": "empty spaces + punctuation included in external stream",
            "use": "Hebrew externally · 64-bit internally",
        },
        "external": {
            "speech": external,
            "stream": stream,
            "hebrew_stream_22": letters,
            "otiyot_count": 22,
            "includes_spaces": any(c in SPACES for c in stream),
            "includes_punct": any(c in PUNCT for c in stream),
            "alphabet_size": BASE,
        },
        "internal": {
            "u64_limbs": limbs,
            "u64_hex": u64_limbs_to_hex(limbs),
            "limb_count": len(limbs),
            "bits_per_limb": 64,
            "chars_per_limb_max": CHARS_PER_U64,
            "base": BASE,
            "base_note": "22 otiyot + spaces + punctuation",
        },
    }
    if op_id is not None:
        ou = canonical_u64(op_id, params or {})
        out["internal"]["op_u64"] = ou
        out["internal"]["op_u64_hex"] = f"{ou:016x}"
        out["internal"]["op_id"] = op_id
    if matches:
        terms = []
        for m in matches:
            fr = m.get("from") or ""
            tl = external_to_u64_limbs(fr)
            terms.append(
                {
                    "id": m.get("id"),
                    "external": fr,
                    "to": m.get("to"),
                    "stream": normalize_external(fr),
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
        "external": "Hebrew + empty spaces + punctuation",
        "internal": "64-bit words (packed limbs + op_u64)",
        "otiyot_22": OTIYOT_22,
        "spaces": ["sp", "tab", "lf", "cr", "nbsp"],
        "punct": PUNCT,
        "alphabet_size": BASE,
        "chars_per_u64": CHARS_PER_U64,
    }
