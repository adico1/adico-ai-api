"""
Machine math ops (programming only).

Registered on-demand via catalog; every run is measure-first → install → execute
and signed to system.ledger (via pipeline / math_event).

Ops: add sub mul div mod pow  (+ numeric list helpers)
"""
from __future__ import annotations

import operator
import re
from typing import Any, Callable

_BIN: dict[str, Callable[[Any, Any], Any]] = {
    "add": operator.add,
    "sub": operator.sub,
    "mul": operator.mul,
    "div": operator.truediv,
    "mod": operator.mod,
    "pow": operator.pow,
}

_SPEECH = {
    "add": ("add", "plus"),
    "sub": ("sub", "subtract", "minus"),
    "mul": ("mul", "multiply", "times"),
    "div": ("div", "divide"),
    "mod": ("mod", "modulo"),
    "pow": ("pow", "power"),
}


def _num(tok: str):
    t = tok.strip()
    if re.fullmatch(r"[+-]?\d+", t):
        return int(t)
    if re.fullmatch(r"[+-]?\d+\.\d+", t):
        return float(t)
    if re.fullmatch(r"0x[0-9a-fA-F]+", t):
        return int(t, 16)
    raise ValueError(f"not_a_number:{tok}")


def parse_binary(raw: str) -> dict:
    """'a b' or 'a, b' or 'a + b' style second number after op word already stripped."""
    s = (raw or "").strip().replace(",", " ")
    # allow a+b without spaces for two ints
    m = re.fullmatch(r"([+-]?(?:0x[0-9a-fA-F]+|\d+\.\d+|\d+))\s*([+\-*/%^]?)\s*([+-]?(?:0x[0-9a-fA-F]+|\d+\.\d+|\d+))", s)
    if m and m.group(2) in ("",):
        return {"a": _num(m.group(1)), "b": _num(m.group(3))}
    parts = [p for p in re.split(r"\s+", s) if p]
    if len(parts) != 2:
        # try a+b
        m2 = re.fullmatch(
            r"([+-]?(?:0x[0-9a-fA-F]+|\d+\.\d+|\d+))\s*[+\-*/%^]\s*([+-]?(?:0x[0-9a-fA-F]+|\d+\.\d+|\d+))",
            s,
        )
        if m2:
            return {"a": _num(m2.group(1)), "b": _num(m2.group(2))}
        raise ValueError("need_two_numbers")
    return {"a": _num(parts[0]), "b": _num(parts[1])}


def run_binary(op: str, params: dict) -> str:
    if op not in _BIN:
        raise KeyError(op)
    a, b = params["a"], params["b"]
    if op == "div" and b == 0:
        return f"div({a}, {b}) = error:div_zero"
    if op == "mod" and b == 0:
        return f"mod({a}, {b}) = error:mod_zero"
    if op == "pow" and isinstance(b, int) and b > 64:
        # keep deterministic and bounded
        return f"pow({a}, {b}) = error:exp_too_large"
    val = _BIN[op](a, b)
    if isinstance(val, float) and val.is_integer():
        val = int(val)
    return f"{op}({a}, {b}) = {val}"


def register_into(catalog_mod) -> None:
    """Register math speech forms on catalog module."""
    for op, words in _SPEECH.items():
        alts = "|".join(words)

        def _make_fn(op_name: str):
            def _fn(params: dict) -> str:
                out = run_binary(op_name, params)
                try:
                    from . import ledger

                    ledger.math_event(
                        f"op.math.{op_name}",
                        {"a": params.get("a"), "b": params.get("b"), "result": out},
                    )
                except Exception:
                    pass
                return out

            return _fn

        patterns = [
            rf"^(?:{alts})\s*\(\s*(.+)\s*\)\s*$",
            rf"^(?:{alts})\s+(.+)\s*$",
        ]
        catalog_mod._reg(
            f"op.math.{op}",
            patterns,
            lambda m, _op=op: parse_binary(m.group(1)),
            _make_fn(op),
        )
        catalog_mod.TALK_FORMS.append(
            {
                "id": f"op.math.{op}",
                "say": [f"{words[0]} a b", f"{words[0]}(a,b)"],
                "params": "two numbers (int/float/0x hex)",
                "computer": f"{op}(a,b) → number",
            }
        )
