# Unified core — strict compliance

## Law

| | |
|---|---|
| **Invent math?** | **No** |
| **Math sources** | Python **built-in / stdlib** (`operator`, `math`, `decimal`) and optional **3rd party** already installed (e.g. `numpy`) |
| **How we use them** | **Bind / clone call** only — thin speech → provider function |
| **Where they run** | Only through the **unified core package** (`adico_ai_api`) |
| **Addresses** | **SY seals** — not truncated SHA “cosmic lottery” |

## SY address (better uniqueness for this system)

| piece | count | role |
|---|---|---|
| **otiyot** | **22** | external letter stream |
| **gates** | **231** = C(22,2) | two-letter combination seals |
| **netivot** | **32** | routing / address bus paths |

### Unique name = cosmic address

| law | meaning |
|---|---|
| **Name of a thing** | **is** its cosmic address (not a label stuck on a separate id) |
| **Same name** | same address · same thing under unified language |
| **New thing** | needs a **new name** (language evolves) |
| **Infinity** | not from a fixed 2⁶⁴ lottery — from **open language growth** |

The 22 · 231 · 32 geometry is the **engine of naming** (how names are formed and routed).  
It is **finite as alphabet**, **infinite as speech**: as the lexicon grows (new SY words, new compounds, new seals), new names appear → new addresses → capacity without end.

```
thing  ↔  unique name  ↔  cosmic address (SY seal)
language evolves  →  new names  →  new addresses
                  →  infinite · infinite · infinity
```

So:

- **Not claimed:** “this u64 is unique across all physics forever by bit count.”  
- **Claimed:** “under this language, the thing’s **only** id is its **name/seal**; evolution of names is evolution of the address space.”

Collision of seals = same name = same thing (correct).  
Truly new thing without a new name cannot be addressed as distinct — **name it** (extend lexicon / compound) first.

### Short human speech vs full system address

Humans may talk in **short language**. Short forms can look the same across fields:

| human (short) | mathematician | physicist |
|---|---|---|
| same words | means **A** | means **B** (different thing) |

The **underlying system always talks in full addresses**:

```text
full_address = short_speech + user + domain + op + seal(thing/about/about2)
```

- Same short speech + **different domain** (e.g. `mathematics` vs `physics`) → **different full addresses**  
- Same short speech + same domain + same user → **same thing**  
- API: pass `domain` / `field` / `discipline` / `olam` with `mi`  

So: seal collision on the **full** name is same thing; short-speech collision alone is **not** enough to identify a thing.

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
