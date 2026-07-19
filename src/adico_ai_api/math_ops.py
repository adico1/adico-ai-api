"""
Math bindings — NOT invented.

Only:
  · Python built-ins / stdlib (operator, math, decimal)
  · optional 3rd party if already installed (e.g. numpy)

Every call is only a thin speech → bind → stdlib/3rd-party call.
All traffic still goes through the unified core package pipeline:
  measure_first → install → execute → cosmos address → ledger

No custom arithmetic algorithms in this package.
"""
from __future__ import annotations

import math
import operator
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

# ── providers (stdlib first; optional 3rd party) ─────────────────
def _stdlib_provider() -> dict[str, Callable[..., Any]]:
    return {
        "add": operator.add,
        "sub": operator.sub,
        "mul": operator.mul,
        "div": operator.truediv,
        "mod": operator.mod,
        "pow": operator.pow,
        "abs": operator.abs,
        "neg": operator.neg,
        "floordiv": operator.floordiv,
        # math module (stdlib)
        "sqrt": math.sqrt,
        "floor": math.floor,
        "ceil": math.ceil,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
    }


def _decimal_provider() -> dict[str, Callable[..., Any]]:
    """stdlib decimal — exact decimal arithmetic, not invented."""

    def dadd(a, b):
        return Decimal(str(a)) + Decimal(str(b))

    def dsub(a, b):
        return Decimal(str(a)) - Decimal(str(b))

    def dmul(a, b):
        return Decimal(str(a)) * Decimal(str(b))

    def ddiv(a, b):
        return Decimal(str(a)) / Decimal(str(b))

    return {
        "decimal_add": dadd,
        "decimal_sub": dsub,
        "decimal_mul": dmul,
        "decimal_div": ddiv,
    }


def _numpy_provider() -> dict[str, Callable[..., Any]] | None:
    try:
        import numpy as np  # type: ignore
    except ImportError:
        return None
    return {
        "np_add": np.add,
        "np_sub": np.subtract,
        "np_mul": np.multiply,
        "np_div": np.true_divide,
        "np_pow": np.power,
        "np_sqrt": np.sqrt,
        "np_sum": np.sum,
    }


_PROVIDERS: list[tuple[str, dict[str, Callable[..., Any]]]] = []
_BIN_NAMES = frozenset(
    {
        "add",
        "sub",
        "mul",
        "div",
        "mod",
        "pow",
        "floordiv",
        "decimal_add",
        "decimal_sub",
        "decimal_mul",
        "decimal_div",
        "np_add",
        "np_sub",
        "np_mul",
        "np_div",
        "np_pow",
    }
)
_UNARY_NAMES = frozenset(
    {"abs", "neg", "sqrt", "floor", "ceil", "log", "log10", "exp", "sin", "cos", "tan", "np_sqrt"}
)


def _rebuild_providers() -> None:
    global _PROVIDERS
    _PROVIDERS = [("stdlib.operator_math", _stdlib_provider()), ("stdlib.decimal", _decimal_provider())]
    np_p = _numpy_provider()
    if np_p:
        _PROVIDERS.append(("third_party.numpy", np_p))


_rebuild_providers()


def list_bindings() -> list[dict[str, Any]]:
    out = []
    for source, table in _PROVIDERS:
        for name, fn in table.items():
            mod = getattr(fn, "__module__", None) or type(fn).__module__
            nm = getattr(fn, "__name__", None) or type(fn).__name__
            out.append(
                {
                    "name": name,
                    "source": source,
                    "arity": (
                        "binary"
                        if name in _BIN_NAMES
                        or (
                            name.startswith("np_")
                            and name not in ("np_sqrt", "np_sum")
                        )
                        else "unary_or_var"
                    ),
                    "invented": False,
                    "callable": f"{mod}.{nm}",
                }
            )
    return out


def resolve(name: str) -> tuple[str, Callable[..., Any]]:
    """Return (provider_source, fn). Raises KeyError if unknown."""
    for source, table in _PROVIDERS:
        if name in table:
            return source, table[name]
    raise KeyError(f"no_binding:{name}")


def _num(tok: str):
    t = tok.strip()
    if re.fullmatch(r"[+-]?\d+", t):
        return int(t)
    if re.fullmatch(r"[+-]?\d+\.\d+", t):
        return float(t)
    if re.fullmatch(r"0x[0-9a-fA-F]+", t):
        return int(t, 16)
    raise ValueError(f"not_a_number:{tok}")


def parse_args(raw: str, arity: str) -> dict:
    s = (raw or "").strip().replace(",", " ")
    parts = [p for p in re.split(r"\s+", s) if p]
    if arity == "unary":
        if len(parts) != 1:
            raise ValueError("need_one_number")
        return {"a": _num(parts[0])}
    # binary
    if len(parts) == 2:
        return {"a": _num(parts[0]), "b": _num(parts[1])}
    m2 = re.fullmatch(
        r"([+-]?(?:0x[0-9a-fA-F]+|\d+\.\d+|\d+))\s*[+\-*/%^]\s*([+-]?(?:0x[0-9a-fA-F]+|\d+\.\d+|\d+))",
        s,
    )
    if m2:
        return {"a": _num(m2.group(1)), "b": _num(m2.group(2))}
    raise ValueError("need_two_numbers")


def run_bound(name: str, params: dict) -> str:
    """Call only the bound stdlib/3rd-party function. No invented math."""
    source, fn = resolve(name)
    try:
        if name in _UNARY_NAMES or name in ("abs", "neg", "sqrt", "floor", "ceil", "log", "log10", "exp", "sin", "cos", "tan", "np_sqrt"):
            a = params["a"]
            val = fn(a)
            shown = f"{name}({a})"
        elif name == "np_sum":
            # third-party reduce
            import numpy as np  # type: ignore

            arr = params.get("numbers") or [params.get("a"), params.get("b")]
            arr = [x for x in arr if x is not None]
            val = fn(np.array(arr, dtype=float))
            shown = f"np_sum({arr})"
        else:
            a, b = params["a"], params["b"]
            val = fn(a, b)
            shown = f"{name}({a}, {b})"
        if isinstance(val, float) and val == int(val) and abs(val) < 1e15:
            val = int(val)
        elif isinstance(val, Decimal):
            val = format(val, "f")
        return f"{shown} = {val}  [provider={source}]"
    except ZeroDivisionError:
        return f"{name}(...) = error:div_zero  [provider={source}]"
    except (OverflowError, ValueError, InvalidOperation) as e:
        return f"{name}(...) = error:{type(e).__name__}  [provider={source}]"


# speech → binding name (machine forms only; not invented ops)
_SPEECH_TO_BIND: list[tuple[str, tuple[str, ...], str]] = [
    # (bind_name, speech_words, arity)
    ("add", ("add", "plus"), "binary"),
    ("sub", ("sub", "subtract", "minus"), "binary"),
    ("mul", ("mul", "multiply", "times"), "binary"),
    ("div", ("div", "divide"), "binary"),
    ("mod", ("mod", "modulo"), "binary"),
    ("pow", ("pow", "power"), "binary"),
    ("floordiv", ("floordiv",), "binary"),
    ("abs", ("abs",), "unary"),
    ("sqrt", ("sqrt",), "unary"),
    ("floor", ("floor",), "unary"),
    ("ceil", ("ceil",), "unary"),
    ("log", ("log",), "unary"),
    ("log10", ("log10",), "unary"),
    ("exp", ("exp",), "unary"),
    ("sin", ("sin",), "unary"),
    ("cos", ("cos",), "unary"),
    ("tan", ("tan",), "unary"),
    ("decimal_add", ("decimal_add",), "binary"),
    ("decimal_mul", ("decimal_mul",), "binary"),
]


def register_into(catalog_mod) -> None:
    """Register speech → bound stdlib/3rd-party only, through unified catalog."""
    _rebuild_providers()
    available = {b["name"] for b in list_bindings()}

    for bind_name, words, arity in _SPEECH_TO_BIND:
        if bind_name not in available:
            continue
        alts = "|".join(re.escape(w) for w in words)

        def _make_fn(bn: str):
            def _fn(params: dict) -> str:
                out = run_bound(bn, params)
                try:
                    from . import ledger

                    src, _ = resolve(bn)
                    ledger.math_event(
                        f"op.math.{bn}",
                        {
                            "binding": bn,
                            "provider": src,
                            "invented": False,
                            "params": {k: params.get(k) for k in ("a", "b") if k in params},
                            "result": out,
                        },
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
            f"op.math.{bind_name}",
            patterns,
            lambda m, ar=arity: parse_args(m.group(1), ar),
            _make_fn(bind_name),
        )
        catalog_mod.TALK_FORMS.append(
            {
                "id": f"op.math.{bind_name}",
                "say": [f"{words[0]} …", f"{words[0]}(…)"],
                "binding": bind_name,
                "invented": False,
                "source": "stdlib or optional third_party via unified core",
                "computer": f"bound {bind_name} — no invented math",
            }
        )

    # optional numpy if present
    if "np_add" in available:
        for bn, words in (
            ("np_add", ("np_add",)),
            ("np_mul", ("np_mul",)),
            ("np_sqrt", ("np_sqrt",)),
        ):
            alts = words[0]

            def _make_np(bn: str, ar: str):
                def _fn(params: dict) -> str:
                    return run_bound(bn, params)

                return _fn

            ar = "unary" if bn == "np_sqrt" else "binary"
            catalog_mod._reg(
                f"op.math.{bn}",
                [rf"^{alts}\s*\(\s*(.+)\s*\)\s*$", rf"^{alts}\s+(.+)\s*$"],
                lambda m, ar=ar: parse_args(m.group(1), ar),
                _make_np(bn, ar),
            )
