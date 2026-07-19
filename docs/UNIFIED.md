# Unified core — strict compliance

## Law

| | |
|---|---|
| **Invent math?** | **No** |
| **Math sources** | Python **built-in / stdlib** (`operator`, `math`, `decimal`) and optional **3rd party** already installed (e.g. `numpy`) |
| **How we use them** | **Bind / clone call** only — thin speech → provider function |
| **Where they run** | Only through the **unified core package** (`adico_ai_api`) |

## Every function (strict path)

```
speech / SY word
  → catalog id
  → measure_first  (system.ledger)
  → install | cache_hit
  → execute  (bound stdlib / 3rd party / SY / address)
  → cosmos address (thing · about · about² · Hebrew)
  → ledger
```

No side path. No free math outside the core. No mystic math.

## What is “ours” vs “theirs”

| ours (unified core) | theirs (not invented here) |
|---|---|
| SY speech · programming map | `operator.add` … |
| measure / install / execute | `math.sqrt` … |
| cosmos address · 64-bit · Hebrew face | `decimal.Decimal` |
| ledger · cache · industry wire | optional `numpy.*` |
| `סכום` / address_sum (address, not inventing Σ theory) | sum of known u64 parts via `operator.add` fold |

## Adding more math

1. Prefer **stdlib** name already in `math` / `operator`.  
2. Or **import 3rd party** if present — register bind in `math_ops.py` providers.  
3. Register speech → bind name only.  
4. Do **not** paste a new arithmetic algorithm into this repo.

## Compliance check

- `invented: false` on all math bindings  
- `provider=` printed on every math answer  
- `GET /v1/talk` → machine_ops list sources  
