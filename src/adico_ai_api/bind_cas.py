"""
CAS / numerics bindings — NOT invented.

φ-step growth toward Wolfram-class *coverage* by binding engines:

  phase φ¹  sympy   (symbolic)
  phase φ²  numpy   (arrays)
  phase φ³  scipy   (scientific numerics)

Every call still goes only through unified core:
  measure_first → install|cache → execute(this bind) → SY full address → ledger
"""
from __future__ import annotations

import re
from typing import Any, Callable

_SYMPY = None
_NUMPY = None
_SCIPY = None


def _try_imports() -> dict[str, bool]:
    global _SYMPY, _NUMPY, _SCIPY
    status = {"sympy": False, "numpy": False, "scipy": False}
    try:
        import sympy as sp

        _SYMPY = sp
        status["sympy"] = True
    except ImportError:
        _SYMPY = None
    try:
        import numpy as np

        _NUMPY = np
        status["numpy"] = True
    except ImportError:
        _NUMPY = None
    try:
        import scipy  # noqa: F401
        import scipy.integrate
        import scipy.optimize
        import scipy.linalg

        _SCIPY = scipy
        status["scipy"] = True
    except ImportError:
        _SCIPY = None
    return status


def provider_status() -> dict[str, Any]:
    st = _try_imports()
    return {
        "phase": "phi_wolfram_bind",
        "invented": False,
        "providers": st,
        "note": "bind engines only; gradual φ expansion toward Wolfram-class coverage",
    }


def _sym(expr: str):
    if _SYMPY is None:
        raise RuntimeError("sympy_not_installed")
    # local dict empty — only sympy namespace (safer than free eval)
    return _SYMPY.sympify(expr, evaluate=True)


def _run_sympy(name: str, params: dict) -> str:
    sp = _SYMPY
    if sp is None:
        return f"{name}(...) = error:sympy_not_installed  [provider=missing]"

    expr = (params.get("expr") or "").strip()
    var = (params.get("var") or "x").strip() or "x"
    try:
        if name == "simplify":
            val = sp.simplify(_sym(expr))
        elif name == "expand":
            val = sp.expand(_sym(expr))
        elif name == "factor":
            val = sp.factor(_sym(expr))
        elif name == "diff":
            x = sp.Symbol(var)
            val = sp.diff(_sym(expr), x)
        elif name == "integrate":
            x = sp.Symbol(var)
            val = sp.integrate(_sym(expr), x)
        elif name == "solve":
            # solve expr for var (expr may be Eq or expression = 0)
            x = sp.Symbol(var)
            e = _sym(expr)
            val = sp.solve(e, x)
        elif name == "limit":
            x = sp.Symbol(var)
            point = params.get("point", "0")
            val = sp.limit(_sym(expr), x, _sym(str(point)))
        elif name == "series":
            x = sp.Symbol(var)
            n = int(params.get("n", 6))
            val = sp.series(_sym(expr), x, 0, n)
        elif name == "nsimplify":
            val = sp.nsimplify(_sym(expr))
        else:
            return f"{name}(...) = error:unknown_bind  [provider=third_party.sympy]"
        return f"{name}({expr}) = {val}  [provider=third_party.sympy]"
    except Exception as e:
        return f"{name}({expr}) = error:{type(e).__name__}:{e}  [provider=third_party.sympy]"


def _run_scipy(name: str, params: dict) -> str:
    if _SCIPY is None or _NUMPY is None:
        return f"{name}(...) = error:scipy_or_numpy_not_installed  [provider=missing]"
    import numpy as np
    from scipy import integrate, optimize, linalg

    try:
        if name == "quad":
            # numerical ∫ f from a to b — f as sympy-able poly string in x
            expr = params.get("expr", "x")
            a = float(params.get("a", 0))
            b = float(params.get("b", 1))
            if _SYMPY is not None:
                sp = _SYMPY
                x = sp.Symbol("x")
                f = sp.lambdify(x, sp.sympify(expr), modules=["numpy"])
            else:
                return f"quad(...) = error:need_sympy_for_expr  [provider=third_party.scipy]"
            val, err = integrate.quad(f, a, b)
            return f"quad({expr},{a},{b}) = {val} ± {err}  [provider=third_party.scipy]"
        if name == "root_scalar":
            expr = params.get("expr", "x")
            a = float(params.get("a", -1))
            b = float(params.get("b", 1))
            sp = _SYMPY
            if sp is None:
                return f"root_scalar(...) = error:need_sympy  [provider=third_party.scipy]"
            x = sp.Symbol("x")
            f = sp.lambdify(x, sp.sympify(expr), modules=["numpy"])
            sol = optimize.root_scalar(f, bracket=[a, b])
            return f"root_scalar({expr}) = {sol.root}  [provider=third_party.scipy]"
        if name == "det":
            # matrix rows: "1 2; 3 4"
            raw = params.get("expr", "1 0; 0 1")
            rows = [[float(x) for x in re.split(r"\s+", r.strip()) if x] for r in raw.split(";")]
            M = np.array(rows, dtype=float)
            return f"det(...) = {linalg.det(M)}  [provider=third_party.scipy]"
        return f"{name}(...) = error:unknown_bind  [provider=third_party.scipy]"
    except Exception as e:
        return f"{name}(...) = error:{type(e).__name__}:{e}  [provider=third_party.scipy]"


def run_bind(name: str, params: dict) -> str:
    _try_imports()
    sympy_names = {
        "simplify",
        "expand",
        "factor",
        "diff",
        "integrate",
        "solve",
        "limit",
        "series",
        "nsimplify",
    }
    scipy_names = {"quad", "root_scalar", "det"}
    if name in sympy_names:
        return _run_sympy(name, params)
    if name in scipy_names:
        return _run_scipy(name, params)
    return f"{name}(...) = error:unknown_bind  [provider=none]"


# speech → (bind_name, arity_style)
# expr forms:  simplify x**2+2*x+1   |  diff sin(x)   |  integrate x**2  |  solve x**2-1
_CAS_SPEECH: list[tuple[str, tuple[str, ...]]] = [
    ("simplify", ("simplify", "sym_simplify")),
    ("expand", ("expand", "sym_expand")),
    ("factor", ("factor", "sym_factor")),
    ("diff", ("diff", "derivative", "d_dx")),
    ("integrate", ("integrate", "int", "integral")),
    ("solve", ("solve", "sym_solve")),
    ("limit", ("limit", "sym_limit")),
    ("series", ("series", "sym_series")),
    ("nsimplify", ("nsimplify",)),
    ("quad", ("quad", "nintegrate")),
    ("root_scalar", ("root_scalar", "nroot")),
    ("det", ("det", "matrix_det")),
]


def _parse_cas_payload(raw: str, name: str) -> dict:
    """
    Forms:
      expr
      expr var
      expr var point   (limit)
      expr a b         (quad / root_scalar bracket)
    """
    s = (raw or "").strip()
    if not s:
        raise ValueError("empty_expr")
    # limit: limit sin(x)/x x 0  OR  limit sin(x)/x 0
    if name == "limit":
        parts = s.rsplit(None, 2)
        if len(parts) == 3 and re.fullmatch(r"[A-Za-z_]\w*", parts[1]):
            return {"expr": parts[0], "var": parts[1], "point": parts[2]}
        if len(parts) >= 2:
            return {"expr": parts[0], "var": "x", "point": parts[-1]}
        return {"expr": s, "var": "x", "point": "0"}
    if name in ("quad", "root_scalar"):
        # integrate_num x**2 0 1
        parts = s.rsplit(None, 2)
        if len(parts) == 3:
            try:
                float(parts[1])
                float(parts[2])
                return {"expr": parts[0], "a": parts[1], "b": parts[2], "var": "x"}
            except ValueError:
                pass
        return {"expr": s, "a": "0", "b": "1", "var": "x"}
    if name in ("diff", "integrate", "solve", "series"):
        parts = s.rsplit(None, 1)
        if len(parts) == 2 and re.fullmatch(r"[A-Za-z_]\w*", parts[1]):
            return {"expr": parts[0], "var": parts[1]}
        return {"expr": s, "var": "x"}
    if name == "det":
        return {"expr": s}
    return {"expr": s}


def register_into(catalog_mod) -> None:
    """Register CAS speech → third-party binds on catalog (unified core only)."""
    st = _try_imports()
    for bind_name, words in _CAS_SPEECH:
        # skip scipy binds if missing
        if bind_name in ("quad", "root_scalar", "det") and not st.get("scipy"):
            continue
        if bind_name not in ("quad", "root_scalar", "det") and not st.get("sympy"):
            continue
        alts = "|".join(re.escape(w) for w in words)

        def _make(bn: str):
            def _fn(params: dict) -> str:
                out = run_bind(bn, params)
                try:
                    from . import ledger

                    ledger.math_event(
                        f"op.cas.{bn}",
                        {
                            "binding": bn,
                            "invented": False,
                            "phase": "phi_wolfram",
                            "result": out[:500],
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
            f"op.cas.{bind_name}",
            patterns,
            lambda m, bn=bind_name: _parse_cas_payload(m.group(1), bn),
            _make(bind_name),
        )
        catalog_mod.TALK_FORMS.append(
            {
                "id": f"op.cas.{bind_name}",
                "say": [f"{words[0]} <expr>", f"{words[0]}(<expr>)"],
                "binding": bind_name,
                "invented": False,
                "phase": "phi¹_sympy" if bind_name not in ("quad", "root_scalar", "det") else "phi³_scipy",
                "source": "third_party.sympy_or_scipy",
            }
        )
