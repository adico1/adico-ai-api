# φ build toward Wolfram-class coverage

**Law:** do not invent CAS. **Bind** engines. Grow coverage **gradually in φ** (each step multiplies capability, det-first through unified core).

## Fixed for every step

```text
short speech + user + domain
  → id → measure_first → install|cache
  → execute(bound provider only)
  → SY full address (22·231·32)
  → ledger
```

No side path. No mystic math. Name = address; language growth = infinity.

## φ phases

| phase | ratio idea | bind | capability |
|---|---|---|---|
| **φ⁰** | 1 | stdlib `operator` / `math` / `decimal` | arithmetic, elementary |
| **φ¹** | ×φ | **SymPy** | simplify, expand, factor, diff, integrate, solve, limit, series |
| **φ²** | ×φ² | **NumPy** | arrays, vectorized numeric |
| **φ³** | ×φ³ | **SciPy** | quad, roots, linalg.det, … |
| **φ⁴** | later | units / datasets (pint, …) | knowledge-ish layer |
| **φ⁵** | later | optional licensed Wolfram engine | true Alpha-class if available |
| **φⁿ** | open | more SY names for each bind | speech grows with language |

φ ≈ 1.618 — each phase is a **larger leap in coverage**, not a rewrite of the core.

## This step (now)

- **φ⁰** already in `math_ops.py`
- **φ¹** SymPy binds in `bind_cas.py` (if installed)
- **φ³** thin SciPy binds when sympy+scipy present
- Roadmap file = this doc

## Install engines (clone/use, not invent)

```bash
pip install 'sympy>=1.12' 'numpy>=1.26' 'scipy>=1.11'
# or: pip install -r requirements-math.txt
```

## Speech examples (machine forms)

```text
simplify (x**2 + 2*x + 1)
expand (x+1)**3
factor x**2-1
diff sin(x)
diff sin(x) x
integrate x**2
solve x**2-1
limit sin(x)/x x 0
series exp(x)
quad x**2 0 1
```

Domain separates short speech:

```json
{"mi":"adi","domain":"mathematics","messages":[{"role":"user","content":"diff sin(x)"}]}
```

## Distance honesty

- After φ¹–φ³: serious **bound** math through the core — **not** yet Wolfram-level product.
- Wolfram-level = decades of CAS + knowledge + UX.
- Our path: **φ steps of binds** + SY naming + unified core compliance.

## Success metric per φ step

1. Provider import true  
2. At least N new binds registered (`invented: false`)  
3. Pipeline + cosmos + ledger still mandatory  
4. Docs list speech forms  
