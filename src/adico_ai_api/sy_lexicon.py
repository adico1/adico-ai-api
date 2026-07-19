"""
Limited Hebrew speech — Sefer Yetzira (Book of Formations) only.

Source lexicon: Adi dictionary (logs) aligned with advanced Creators SY repo.
Not multi-lingual. Not free Hebrew. Only terms in the sealed lexicon.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_LEX: dict | None = None
_TERMS_SORTED: list[dict] = []

# default pack shipped in package; override with ADICO_SY_LEXICON
_DEFAULT = Path(__file__).resolve().parent / "lexicon" / "sefer_yetzira_limited_he.json"
# optional live advanced tree (owner machine) — docs only / future expand
ADVANCED_SY = Path("/Users/adicohen/work/extension/advanced/SY")


def _load() -> dict:
    global _LEX, _TERMS_SORTED
    if _LEX is not None:
        return _LEX
    import os

    path = Path(os.environ.get("ADICO_SY_LEXICON", str(_DEFAULT))).expanduser()
    if not path.is_file():
        path = _DEFAULT
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = list(data.get("entries") or [])
    # longest term first so "אות בשם" wins over shorter fragments
    entries.sort(key=lambda e: len(e.get("from") or ""), reverse=True)
    _LEX = data
    _TERMS_SORTED = entries
    return data


def lexicon_meta() -> dict[str, Any]:
    d = _load()
    return {
        "schema": d.get("schema"),
        "source_book": d.get("source_book"),
        "source_advanced": d.get("source_advanced"),
        "rule": d.get("rule"),
        "entry_count": len(d.get("entries") or []),
        "advanced_sy_present": ADVANCED_SY.is_dir(),
        "lexicon_path": str(
            Path(__import__("os").environ.get("ADICO_SY_LEXICON", str(_DEFAULT))).expanduser()
            if __import__("os").environ.get("ADICO_SY_LEXICON")
            else _DEFAULT
        ),
    }


def match_terms(text: str) -> list[dict]:
    """Find lexicon terms inside text (limited Hebrew only)."""
    _load()
    t = text or ""
    if not t.strip():
        return []
    used_spans: list[tuple[int, int]] = []
    matches: list[dict] = []
    for e in _TERMS_SORTED:
        term = e.get("from") or ""
        if not term:
            continue
        start = 0
        while True:
            i = t.find(term, start)
            if i < 0:
                break
            j = i + len(term)
            # skip overlapping spans
            if any(not (j <= a or i >= b) for a, b in used_spans):
                start = i + 1
                continue
            used_spans.append((i, j))
            matches.append(
                {
                    "id": e["id"],
                    "from": term,
                    "to": e.get("to"),
                    "kind": e.get("kind"),
                    "verse_ref": e.get("verse_ref"),
                    "span": [i, j],
                }
            )
            start = j
    # stable order by appearance in text
    matches.sort(key=lambda m: m["span"][0])
    return matches


def translate_input(text: str) -> dict | None:
    """
    If input contains ≥1 lexicon term → sealed op sy.lexicon.translate.
    Pure English sealed forms are handled elsewhere; here only SY Hebrew hits.
    """
    matches = match_terms(text)
    if not matches:
        return None
    return {
        "id": "sy.lexicon.translate",
        "params": {
            "matches": [
                {
                    "id": m["id"],
                    "from": m["from"],
                    "to": m["to"],
                    "kind": m["kind"],
                    "verse_ref": m.get("verse_ref"),
                }
                for m in matches
            ],
            "raw": text,
        },
        "question_of_question": text.strip(),
    }


def execute_translate(params: dict) -> str:
    matches = params.get("matches") or []
    if not matches:
        return "sy.lexicon.translate: empty"
    lines = ["Book of Formations · limited Hebrew → computer language:"]
    for m in matches:
        lines.append(f"  · {m.get('from')} → {m.get('to')}  [{m.get('id')}|{m.get('kind')}]")
    lines.append(f"match_count={len(matches)}")
    lines.append("source=sefer_yetzira_limited_he · not multi-lingual free speech")
    return "\n".join(lines)


def talk_forms() -> list[dict]:
    _load()
    # sample teaching forms: each term is a valid utterance
    samples = []
    for e in (_LEX or {}).get("entries") or []:
        samples.append(
            {
                "id": f"sy.{e['id']}",
                "say": [e["from"], f"(with others) …{e['from']}…"],
                "to": e["to"],
                "kind": e.get("kind"),
            }
        )
    return samples
