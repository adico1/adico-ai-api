"""
Sealed op catalog.

Books / symbolic sources extend this (potential → act).
Today: built-in sealed ids only — no invention of freeform truth.
"""
from __future__ import annotations

import ast
import datetime as _dt
import hashlib
import json
import operator
import re
from pathlib import Path
from typing import Any, Callable

from . import config

# op_id → handler(params) -> str answer
_OPS: dict[str, Callable[[dict], str]] = {}
# phrase / pattern → (op_id, param_extractor)
_ROUTES: list[tuple[re.Pattern, str, Callable[[re.Match], dict]]] = []


def _reg(op_id: str, patterns: list[str], extract: Callable[[re.Match], dict], fn: Callable[[dict], str]):
    _OPS[op_id] = fn
    for p in patterns:
        _ROUTES.append((re.compile(p, re.I | re.S), op_id, extract))


def _calc(node):
    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.FloorDiv: operator.floordiv,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    if isinstance(node, ast.Expression):
        return _calc(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in ops:
        return ops[type(node.op)](_calc(node.left), _calc(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in ops:
        return ops[type(node.op)](_calc(node.operand))
    raise ValueError("unsupported")


def _arith(params: dict) -> str:
    expr = params["expr"]
    val = _calc(ast.parse(expr, mode="eval"))
    return f"{expr} = {val}"


def _now(_params: dict) -> str:
    return "now=" + _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _date(_params: dict) -> str:
    return "date=" + _dt.datetime.now().strftime("%Y-%m-%d")


def _sha(params: dict) -> str:
    return "sha256=" + hashlib.sha256(params["text"].encode("utf-8")).hexdigest()


def _len(params: dict) -> str:
    return "len=" + str(len(params["text"]))


def _rev(params: dict) -> str:
    return "reversed=" + params["text"][::-1]


def _echo_identity(_params: dict) -> str:
    return "name=adico-ops · company=adico · deterministic catalog · local data"


def _install_mark(params: dict) -> str:
    """Record that an id is installed (local catalog extension placeholder)."""
    return f"installed_id={params.get('target_id', '')}"


# --- routes: questions-of-question → id ---
_reg(
    "op.arith",
    [r"^(?:calc|חשב|=)?\s*([0-9eE.\+\-\*/%\(\)\s]+)\s*\??\s*$"],
    lambda m: {"expr": re.sub(r"\s*=\s*\?\s*$", "", m.group(1)).strip().rstrip("?")},
    _arith,
)
_reg(
    "op.time.now",
    [r"^(?:what\s+is\s+the\s+)?(?:time|clock|now)\b", r"(?:שעה|עכשיו)"],
    lambda m: {},
    _now,
)
_reg(
    "op.date.today",
    [r"^(?:what\s+is\s+)?(?:the\s+)?(?:date|today)\b", r"(?:תאריך|היום)"],
    lambda m: {},
    _date,
)
_reg(
    "op.hash.sha256",
    [r"^(?:hash|sha256|hsh)\s+(.+)$"],
    lambda m: {"text": m.group(1)},
    _sha,
)
_reg(
    "op.text.len",
    [r"^(?:len|אורך)\s+(.+)$"],
    lambda m: {"text": m.group(1)},
    _len,
)
_reg(
    "op.text.reverse",
    [r"^(?:reverse|הפוך)\s+(.+)$"],
    lambda m: {"text": m.group(1)},
    _rev,
)
_reg(
    "op.identity",
    [r"^(?:who\s+are\s+you|what\s+are\s+you|מי אתה|מה שמך)", r"^your\s+name\b"],
    lambda m: {},
    _echo_identity,
)
_reg(
    "op.catalog.install",
    [r"^(?:install\s+id|install_id)\s+(\S+)$"],
    lambda m: {"target_id": m.group(1)},
    _install_mark,
)


def _load_extra() -> None:
    p = config.CATALOG_EXTRA
    if not p.is_file():
        return
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return
    # extra file may list static answers only (no code load — safety)
    for entry in data.get("ops") or []:
        op_id = entry.get("id")
        answer = entry.get("answer")
        patterns = entry.get("patterns") or []
        if not op_id or answer is None:
            continue
        if op_id in _OPS:
            continue

        def _fn(params: dict, _a=answer) -> str:
            return str(_a)

        _OPS[op_id] = _fn
        for pat in patterns:
            try:
                _ROUTES.append((re.compile(pat, re.I | re.S), op_id, lambda m: {}))
            except re.error:
                continue


_load_extra()


def translate(text: str) -> dict | None:
    """
    questions-of-question → id + params.
    Returns None if no sealed id (not invented).
    """
    t = (text or "").strip()
    if not t:
        return None
    # strip trailing ? for arith etc already in patterns
    for rx, op_id, extract in _ROUTES:
        m = rx.search(t)
        if not m:
            continue
        # for full-match preference: if pattern is ^...$ style, search is fine
        try:
            params = extract(m)
        except Exception:
            params = {}
        # arith guard: must look like expression
        if op_id == "op.arith":
            expr = (params.get("expr") or "").strip()
            if not expr or not any(c.isdigit() for c in expr) or not any(o in expr for o in "+-*/%"):
                continue
            try:
                _calc(ast.parse(expr, mode="eval"))
            except Exception:
                continue
        return {"id": op_id, "params": params, "question_of_question": t}
    return None


def installed(op_id: str) -> bool:
    return op_id in _OPS


def install(op_id: str) -> dict:
    """
    On-demand install: ensure op is present in process catalog.
    Extra static ops load from ADICO_CATALOG file at startup; here we only verify.
    """
    ok = op_id in _OPS
    return {"id": op_id, "installed": ok, "source": "builtin_or_extra" if ok else "missing"}


def execute(op_id: str, params: dict) -> str:
    fn = _OPS.get(op_id)
    if fn is None:
        raise KeyError(f"op not installed: {op_id}")
    return fn(params or {})


def list_ops() -> list[str]:
    return sorted(_OPS.keys())
