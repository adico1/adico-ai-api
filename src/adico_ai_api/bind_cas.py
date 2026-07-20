"""
CAS / numerics bindings — NOT invented.

φ growth toward Wolfram-class *coverage* by binding engines:

  φ⁰  stdlib (math_ops.py)
  φ¹  sympy   symbolic
  φ²  numpy   arrays / linalg basics
  φ³  scipy   scientific numerics
  φⁿ  more binds + SY names — never invent CAS here

Unified core only:
  measure_first → install|cache → execute(bind) → SY full address → ledger
"""
from __future__ import annotations

import re
from typing import Any

_SYMPY = None
_NUMPY = None
_SCIPY = None

# --- speech registry: (bind_name, words, engine, phase) ---
# engine: sympy | numpy | scipy
_CAS_SPEECH: list[tuple[str, tuple[str, ...], str, str]] = [
    # φ¹ sympy — algebra / calculus
    ("simplify", ("simplify", "sym_simplify"), "sympy", "phi1"),
    ("expand", ("expand", "sym_expand"), "sympy", "phi1"),
    ("factor", ("factor", "sym_factor"), "sympy", "phi1"),
    ("collect", ("collect", "sym_collect"), "sympy", "phi1"),
    ("cancel", ("cancel", "sym_cancel"), "sympy", "phi1"),
    ("apart", ("apart", "partial_fractions"), "sympy", "phi1"),
    ("together", ("together", "sym_together"), "sympy", "phi1"),
    ("trigsimp", ("trigsimp",), "sympy", "phi1"),
    ("powsimp", ("powsimp",), "sympy", "phi1"),
    ("diff", ("diff", "derivative", "d_dx"), "sympy", "phi1"),
    ("integrate", ("integrate", "int", "integral"), "sympy", "phi1"),
    ("solve", ("solve", "sym_solve"), "sympy", "phi1"),
    ("dsolve", ("dsolve", "ode"), "sympy", "phi1"),
    ("limit", ("limit", "sym_limit"), "sympy", "phi1"),
    ("series", ("series", "sym_series"), "sympy", "phi1"),
    ("summation", ("summation", "sym_sum"), "sympy", "phi1"),
    ("product", ("product", "sym_product"), "sympy", "phi1"),
    ("subs", ("subs", "substitute"), "sympy", "phi1"),
    ("evalf", ("evalf", "N", "numeric"), "sympy", "phi1"),
    ("nsimplify", ("nsimplify",), "sympy", "phi1"),
    ("latex", ("latex", "sym_latex"), "sympy", "phi1"),
    ("gcd", ("gcd", "sym_gcd"), "sympy", "phi1"),
    ("lcm", ("lcm", "sym_lcm"), "sympy", "phi1"),
    ("factorial", ("factorial", "fact"), "sympy", "phi1"),
    ("binomial", ("binomial", "binoms"), "sympy", "phi1"),
    ("matrix", ("matrix", "Matrix"), "sympy", "phi1"),
    ("eigenvals", ("eigenvals", "eigenvalues"), "sympy", "phi1"),
    ("eigenvects", ("eigenvects", "eigenvectors"), "sympy", "phi1"),
    ("inv", ("inv", "inverse", "matrix_inv"), "sympy", "phi1"),
    ("transpose", ("transpose", "T"), "sympy", "phi1"),
    ("det_sym", ("det_sym", "sym_det"), "sympy", "phi1"),
    ("rref", ("rref",), "sympy", "phi1"),
    # φ² numpy
    ("np_mean", ("np_mean", "mean"), "numpy", "phi2"),
    ("np_std", ("np_std", "std"), "numpy", "phi2"),
    ("np_dot", ("np_dot", "dot"), "numpy", "phi2"),
    ("np_matmul", ("np_matmul", "matmul"), "numpy", "phi2"),
    ("np_norm", ("np_norm", "norm"), "numpy", "phi2"),
    ("np_sum", ("np_sum",), "numpy", "phi2"),
    ("np_linspace", ("np_linspace", "linspace"), "numpy", "phi2"),
    # φ³ scipy
    ("quad", ("quad", "nintegrate"), "scipy", "phi3"),
    ("root_scalar", ("root_scalar", "nroot"), "scipy", "phi3"),
    ("det", ("det", "matrix_det"), "scipy", "phi3"),
    ("eig", ("eig", "scipy_eig"), "scipy", "phi3"),
    ("fft", ("fft", "scipy_fft"), "scipy", "phi3"),
]


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
        import scipy.fft

        _SCIPY = scipy
        status["scipy"] = True
    except ImportError:
        _SCIPY = None
    return status


def provider_status() -> dict[str, Any]:
    st = _try_imports()
    available = []
    for name, words, eng, phase in _CAS_SPEECH:
        if eng == "sympy" and st["sympy"]:
            available.append(name)
        elif eng == "numpy" and st["numpy"]:
            available.append(name)
        elif eng == "scipy" and st["scipy"] and st["numpy"]:
            available.append(name)
    return {
        "phase": "phi_wolfram_bind",
        "invented": False,
        "providers": st,
        "binds_registered_when_loaded": available,
        "bind_count": len(available),
        "note": "bind engines only; φ growth toward Wolfram-class coverage",
        "docs": "docs/PHI_WOLFRAM.md",
    }


def _sym(expr: str):
    if _SYMPY is None:
        raise RuntimeError("sympy_not_installed")
    return _SYMPY.sympify(expr, evaluate=True)


def _parse_matrix(raw: str):
    """'1 2; 3 4' → sympy Matrix or numpy array rows."""
    rows = []
    for r in raw.split(";"):
        r = r.strip()
        if not r:
            continue
        rows.append([x for x in re.split(r"[\s,]+", r) if x])
    return rows


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
        elif name == "collect":
            x = sp.Symbol(var)
            val = sp.collect(_sym(expr), x)
        elif name == "cancel":
            val = sp.cancel(_sym(expr))
        elif name == "apart":
            x = sp.Symbol(var)
            val = sp.apart(_sym(expr), x)
        elif name == "together":
            val = sp.together(_sym(expr))
        elif name == "trigsimp":
            val = sp.trigsimp(_sym(expr))
        elif name == "powsimp":
            val = sp.powsimp(_sym(expr))
        elif name == "diff":
            x = sp.Symbol(var)
            n = int(params.get("n", 1))
            val = sp.diff(_sym(expr), x, n)
        elif name == "integrate":
            x = sp.Symbol(var)
            val = sp.integrate(_sym(expr), x)
        elif name == "solve":
            x = sp.Symbol(var)
            val = sp.solve(_sym(expr), x)
        elif name == "dsolve":
            # dsolve f(x).diff(x) - f(x)  OR  Eq form in expr; function f
            f = sp.Function("f")
            x = sp.Symbol(var)
            # allow f for unknown
            e = sp.sympify(expr, locals={"f": f, "x": x, "diff": sp.diff})
            val = sp.dsolve(e, f(x))
        elif name == "limit":
            x = sp.Symbol(var)
            point = params.get("point", "0")
            val = sp.limit(_sym(expr), x, _sym(str(point)))
        elif name == "series":
            x = sp.Symbol(var)
            n = int(params.get("n", 6))
            val = sp.series(_sym(expr), x, 0, n)
        elif name == "summation":
            # summation k**2 k 1 10
            k = sp.Symbol(params.get("var", "k"))
            a = _sym(str(params.get("a", "1")))
            b = _sym(str(params.get("b", "n")))
            val = sp.summation(_sym(expr), (k, a, b))
        elif name == "product":
            k = sp.Symbol(params.get("var", "k"))
            a = _sym(str(params.get("a", "1")))
            b = _sym(str(params.get("b", "n")))
            val = sp.product(_sym(expr), (k, a, b))
        elif name == "subs":
            # subs x**2+1 x 3  → expr, old, new
            old = params.get("old", "x")
            new = params.get("new", "0")
            val = _sym(expr).subs(_sym(str(old)), _sym(str(new)))
        elif name == "evalf":
            n = int(params.get("n", 15))
            val = _sym(expr).evalf(n)
        elif name == "nsimplify":
            val = sp.nsimplify(_sym(expr))
        elif name == "latex":
            val = sp.latex(_sym(expr))
        elif name == "gcd":
            # gcd a b
            a = _sym(params.get("a", expr.split()[0] if expr.split() else "0"))
            b = _sym(params.get("b", expr.split()[1] if len(expr.split()) > 1 else "1"))
            val = sp.gcd(a, b)
        elif name == "lcm":
            a = _sym(params.get("a", "2"))
            b = _sym(params.get("b", "3"))
            if " " in expr and "a" not in params:
                parts = expr.split()
                if len(parts) >= 2:
                    a, b = _sym(parts[0]), _sym(parts[1])
            val = sp.lcm(a, b)
        elif name == "factorial":
            val = sp.factorial(_sym(expr))
        elif name == "binomial":
            # binomial n k
            parts = expr.split()
            if len(parts) >= 2:
                val = sp.binomial(_sym(parts[0]), _sym(parts[1]))
            else:
                val = sp.binomial(_sym(params.get("a", "n")), _sym(params.get("b", "k")))
        elif name in ("matrix", "eigenvals", "eigenvects", "inv", "transpose", "det_sym", "rref"):
            rows = _parse_matrix(expr)
            M = sp.Matrix([[_sym(c) for c in row] for row in rows])
            if name == "matrix":
                val = M
            elif name == "eigenvals":
                val = M.eigenvals()
            elif name == "eigenvects":
                val = M.eigenvects()
            elif name == "inv":
                val = M.inv()
            elif name == "transpose":
                val = M.T
            elif name == "det_sym":
                val = M.det()
            elif name == "rref":
                val = M.rref()
        else:
            return f"{name}(...) = error:unknown_bind  [provider=third_party.sympy]"
        return f"{name}({expr}) = {val}  [provider=third_party.sympy]"
    except Exception as e:
        return f"{name}({expr}) = error:{type(e).__name__}:{e}  [provider=third_party.sympy]"


def _run_numpy(name: str, params: dict) -> str:
    if _NUMPY is None:
        return f"{name}(...) = error:numpy_not_installed  [provider=missing]"
    import numpy as np

    expr = (params.get("expr") or "").strip()
    try:
        if name == "np_linspace":
            # linspace 0 1 5
            parts = expr.split()
            a, b, n = float(parts[0]), float(parts[1]), int(parts[2]) if len(parts) > 2 else 50
            val = np.linspace(a, b, n)
            return f"np_linspace({a},{b},{n}) = {val}  [provider=third_party.numpy]"
        # vector from spaces: 1 2 3 4
        if name in ("np_mean", "np_std", "np_sum", "np_norm"):
            arr = np.array([float(x) for x in re.split(r"[\s,;]+", expr) if x], dtype=float)
            if name == "np_mean":
                val = np.mean(arr)
            elif name == "np_std":
                val = np.std(arr)
            elif name == "np_sum":
                val = np.sum(arr)
            else:
                val = np.linalg.norm(arr)
            return f"{name}({list(arr)}) = {val}  [provider=third_party.numpy]"
        if name in ("np_dot", "np_matmul"):
            # 1 2 3 | 4 5 6
            if "|" not in expr:
                return f"{name}(...) = error:need_a|b_vectors  [provider=third_party.numpy]"
            left, right = expr.split("|", 1)
            a = np.array([float(x) for x in re.split(r"[\s,]+", left.strip()) if x])
            b = np.array([float(x) for x in re.split(r"[\s,]+", right.strip()) if x])
            if name == "np_dot":
                val = np.dot(a, b)
            else:
                # matmul: rows of A ; separated, | B
                if ";" in left:
                    A = np.array(
                        [[float(x) for x in re.split(r"\s+", r.strip()) if x] for r in left.split(";")],
                        dtype=float,
                    )
                    B = np.array(
                        [[float(x) for x in re.split(r"\s+", r.strip()) if x] for r in right.split(";")],
                        dtype=float,
                    )
                    val = np.matmul(A, B)
                else:
                    val = np.matmul(a, b)
            return f"{name}(...) = {val}  [provider=third_party.numpy]"
        return f"{name}(...) = error:unknown_bind  [provider=third_party.numpy]"
    except Exception as e:
        return f"{name}(...) = error:{type(e).__name__}:{e}  [provider=third_party.numpy]"


def _run_scipy(name: str, params: dict) -> str:
    if _SCIPY is None or _NUMPY is None:
        return f"{name}(...) = error:scipy_or_numpy_not_installed  [provider=missing]"
    import numpy as np
    from scipy import integrate, optimize, linalg, fft

    expr = params.get("expr", "x")
    try:
        if name == "quad":
            a = float(params.get("a", 0))
            b = float(params.get("b", 1))
            if _SYMPY is None:
                return f"quad(...) = error:need_sympy_for_expr  [provider=third_party.scipy]"
            sp = _SYMPY
            x = sp.Symbol("x")
            f = sp.lambdify(x, sp.sympify(expr), modules=["numpy"])
            val, err = integrate.quad(f, a, b)
            return f"quad({expr},{a},{b}) = {val} ± {err}  [provider=third_party.scipy]"
        if name == "root_scalar":
            a = float(params.get("a", -1))
            b = float(params.get("b", 1))
            if _SYMPY is None:
                return f"root_scalar(...) = error:need_sympy  [provider=third_party.scipy]"
            sp = _SYMPY
            x = sp.Symbol("x")
            f = sp.lambdify(x, sp.sympify(expr), modules=["numpy"])
            sol = optimize.root_scalar(f, bracket=[a, b])
            return f"root_scalar({expr}) = {sol.root}  [provider=third_party.scipy]"
        if name == "det":
            rows = [[float(x) for x in re.split(r"\s+", r.strip()) if x] for r in str(expr).split(";")]
            M = np.array(rows, dtype=float)
            return f"det(...) = {linalg.det(M)}  [provider=third_party.scipy]"
        if name == "eig":
            rows = [[float(x) for x in re.split(r"\s+", r.strip()) if x] for r in str(expr).split(";")]
            M = np.array(rows, dtype=float)
            w, v = linalg.eig(M)
            return f"eig(...) = eigenvalues={w}  [provider=third_party.scipy]"
        if name == "fft":
            arr = np.array([float(x) for x in re.split(r"[\s,;]+", str(expr)) if x], dtype=float)
            val = fft.fft(arr)
            return f"fft(...) = {val}  [provider=third_party.scipy]"
        return f"{name}(...) = error:unknown_bind  [provider=third_party.scipy]"
    except Exception as e:
        return f"{name}(...) = error:{type(e).__name__}:{e}  [provider=third_party.scipy]"


def run_bind(name: str, params: dict) -> str:
    _try_imports()
    meta = {n: (e, p) for n, _w, e, p in _CAS_SPEECH}
    if name not in meta:
        return f"{name}(...) = error:unknown_bind  [provider=none]"
    eng, _phase = meta[name]
    if eng == "sympy":
        return _run_sympy(name, params)
    if eng == "numpy":
        return _run_numpy(name, params)
    if eng == "scipy":
        return _run_scipy(name, params)
    return f"{name}(...) = error:unknown_engine  [provider=none]"


def _parse_cas_payload(raw: str, name: str) -> dict:
    s = (raw or "").strip()
    if not s:
        raise ValueError("empty_expr")

    if name == "limit":
        parts = s.rsplit(None, 2)
        if len(parts) == 3 and re.fullmatch(r"[A-Za-z_]\w*", parts[1]):
            return {"expr": parts[0], "var": parts[1], "point": parts[2]}
        if len(parts) >= 2:
            return {"expr": parts[0], "var": "x", "point": parts[-1]}
        return {"expr": s, "var": "x", "point": "0"}

    if name in ("quad", "root_scalar"):
        parts = s.rsplit(None, 2)
        if len(parts) == 3:
            try:
                float(parts[1])
                float(parts[2])
                return {"expr": parts[0], "a": parts[1], "b": parts[2], "var": "x"}
            except ValueError:
                pass
        return {"expr": s, "a": "0", "b": "1", "var": "x"}

    if name in ("summation", "product"):
        # summation k**2 k 1 10
        parts = s.split()
        if len(parts) >= 4 and re.fullmatch(r"[A-Za-z_]\w*", parts[1]):
            return {
                "expr": parts[0],
                "var": parts[1],
                "a": parts[2],
                "b": parts[3],
            }
        return {"expr": s, "var": "k", "a": "1", "b": "n"}

    if name == "subs":
        # subs x**2+1 x 3
        parts = s.rsplit(None, 2)
        if len(parts) == 3:
            return {"expr": parts[0], "old": parts[1], "new": parts[2]}
        return {"expr": s, "old": "x", "new": "0"}

    if name in ("gcd", "lcm", "binomial") and name != "binomial":
        parts = s.split()
        if len(parts) >= 2:
            return {"expr": s, "a": parts[0], "b": parts[1]}
        return {"expr": s}

    if name == "binomial":
        parts = s.split()
        if len(parts) >= 2:
            return {"expr": s, "a": parts[0], "b": parts[1]}
        return {"expr": s}

    if name in ("diff", "integrate", "solve", "series", "collect", "apart", "dsolve"):
        parts = s.rsplit(None, 1)
        if len(parts) == 2 and re.fullmatch(r"[A-Za-z_]\w*", parts[1]):
            return {"expr": parts[0], "var": parts[1]}
        return {"expr": s, "var": "x"}

    if name == "evalf":
        parts = s.rsplit(None, 1)
        if len(parts) == 2 and parts[1].isdigit():
            return {"expr": parts[0], "n": parts[1]}
        return {"expr": s, "n": "15"}

    # matrix-like and default
    return {"expr": s}


def register_into(catalog_mod) -> None:
    """Register CAS speech → third-party binds (unified core only)."""
    st = _try_imports()
    for bind_name, words, eng, phase in _CAS_SPEECH:
        if eng == "sympy" and not st.get("sympy"):
            continue
        if eng == "numpy" and not st.get("numpy"):
            continue
        if eng == "scipy" and not (st.get("scipy") and st.get("numpy")):
            continue
        alts = "|".join(re.escape(w) for w in words)

        def _make(bn: str, ph: str):
            def _fn(params: dict) -> str:
                out = run_bind(bn, params)
                try:
                    from . import ledger

                    ledger.math_event(
                        f"op.cas.{bn}",
                        {
                            "binding": bn,
                            "invented": False,
                            "phase": ph,
                            "result": out[:500],
                        },
                    )
                except Exception:
                    pass
                return out

            return _fn

        # Prefer "name <expr>" so expressions with parentheses parse whole.
        # Outer-wrap form only when entire args are one (...).
        patterns = [
            rf"^(?:{alts})\((.+)\)\s*$",
            rf"^(?:{alts})\s+(.+)\s*$",
        ]
        catalog_mod._reg(
            f"op.cas.{bind_name}",
            patterns,
            lambda m, bn=bind_name: _parse_cas_payload(m.group(1), bn),
            _make(bind_name, phase),
        )
        catalog_mod.TALK_FORMS.append(
            {
                "id": f"op.cas.{bind_name}",
                "say": [f"{words[0]} <expr>", f"{words[0]}(<expr>)"],
                "binding": bind_name,
                "invented": False,
                "phase": phase,
                "engine": eng,
                "source": f"third_party.{eng}",
            }
        )
