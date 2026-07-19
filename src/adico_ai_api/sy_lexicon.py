"""
SY speech only → programming terms only.

- External speech: Sefer Yetzira lexicon words only (optional ו- prefix).
- Internal map: computers / programming terms only (no mysticism).
- Not multi-lingual. Not free Hebrew.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_LEX: dict | None = None
_TERMS_SORTED: list[dict] = []

_DEFAULT = Path(__file__).resolve().parent / "lexicon" / "sefer_yetzira_limited_he.json"
ADVANCED_SY = Path("/Users/adicohen/work/extension/advanced/SY")

# programming term: snake_case or known tech tokens only
_PROG_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _load() -> dict:
    global _LEX, _TERMS_SORTED
    if _LEX is not None:
        return _LEX
    import os

    path = Path(os.environ.get("ADICO_SY_LEXICON", str(_DEFAULT))).expanduser()
    if not path.is_file():
        path = _DEFAULT
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = []
    for e in data.get("entries") or []:
        fr = (e.get("from") or "").strip()
        to = (e.get("to") or "").strip()
        if not fr or not to:
            continue
        # reject non-programming targets (must stay technological)
        if not _PROG_RE.match(to):
            continue
        # reject English-looking speech forms — SY words only for `from`
        if re.search(r"[A-Za-z]", fr):
            continue
        entries.append(
            {
                "id": e.get("id"),
                "from": fr,
                "to": to,
                "kind": e.get("kind") or "term",
            }
        )
    entries.sort(key=lambda e: len(e.get("from") or ""), reverse=True)
    _LEX = {
        "schema": data.get("schema"),
        "source_book": data.get("source_book"),
        "source_advanced": data.get("source_advanced"),
        "rule": data.get("rule"),
        "speech": "sy_words_only",
        "target": "programming_terms_only",
        "entries": entries,
    }
    _TERMS_SORTED = entries
    return _LEX


def lexicon_meta() -> dict[str, Any]:
    d = _load()
    return {
        "schema": d.get("schema"),
        "speech": "sy_words_only",
        "target": "programming_terms_only",
        "source_book": d.get("source_book"),
        "source_advanced": d.get("source_advanced"),
        "rule": d.get("rule"),
        "entry_count": len(d.get("entries") or []),
        "advanced_sy_present": ADVANCED_SY.is_dir(),
        "words": [e["from"] for e in d.get("entries") or []],
        "programming_terms": [e["to"] for e in d.get("entries") or []],
    }


def match_terms(text: str) -> list[dict]:
    """Match SY words only (optional Hebrew ו-and prefix)."""
    _load()
    t = text or ""
    if not t.strip():
        return []
    used_spans: list[tuple[int, int]] = []
    matches: list[dict] = []
    for e in _TERMS_SORTED:
        term = e["from"]
        forms = [term]
        if not term.startswith("ו"):
            forms.append("ו" + term)
        for form in forms:
            start = 0
            while True:
                i = t.find(form, start)
                if i < 0:
                    break
                j = i + len(form)
                if any(not (j <= a or i >= b) for a, b in used_spans):
                    start = i + 1
                    continue
                used_spans.append((i, j))
                matches.append(
                    {
                        "id": e["id"],
                        "from": term,
                        "surface": form,
                        "to": e["to"],
                        "kind": e["kind"],
                        "span": [i, j],
                    }
                )
                start = j
    matches.sort(key=lambda m: m["span"][0])
    return matches


def translate_input(text: str) -> dict | None:
    """SY words present → sy.lexicon.translate. Else None."""
    matches = match_terms(text)
    if not matches:
        return None
    # reject if the utterance is only punctuation/spaces aside from matches? allow mixed SY
    return {
        "id": "sy.lexicon.translate",
        "params": {
            "matches": [
                {
                    "id": m["id"],
                    "from": m["from"],
                    "surface": m.get("surface") or m["from"],
                    "to": m["to"],
                    "kind": m["kind"],
                }
                for m in matches
            ],
            "raw": text,
        },
        "question_of_question": text.strip(),
    }


def execute_translate(params: dict) -> str:
    """Programming pipeline only — no mystic wording."""
    from . import bits64

    matches = params.get("matches") or []
    if not matches:
        return "error: empty_sy_match"
    pipeline_words = [str(m.get("to") or "") for m in matches]
    lines = [
        "programming:",
        "  " + " -> ".join(pipeline_words),
        "",
        "sy_word -> programming_term:",
    ]
    for m in matches:
        fr = m.get("from") or ""
        surf = m.get("surface") or fr
        limbs = bits64.hebrew_to_u64_limbs(fr)
        hx = bits64.u64_limbs_to_hex(limbs)[0]
        extra = f" surface={surf}" if surf != fr else ""
        lines.append(f"  {fr} = {m.get('to')}{extra}  id={m.get('id')}  u64=0x{hx}")
    lines.append("")
    lines.append(f"match_count={len(matches)}")
    lines.append("speech=sy_words_only target=programming_terms_only internal=u64")
    return "\n".join(lines)


def talk_forms() -> list[dict]:
    _load()
    return [
        {
            "id": f"sy.{e['id']}",
            "say": [e["from"], "ו" + e["from"] if not e["from"].startswith("ו") else e["from"]],
            "programming": e["to"],
            "kind": e.get("kind"),
        }
        for e in (_LEX or {}).get("entries") or []
    ]
