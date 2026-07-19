# How to talk to adico-ops (this stage)

**Not multi-lingual.**  
Speech is **learned sealed forms** → **ids**. Free chat is not the product.

### Representation law

| face | medium |
|---|---|
| **External** | Hebrew — 22-letter combinations (Sefer Yetzira simplification) |
| **Internal** | **64-bit** words (Babylonian machine face) |

Babylonians spoke 64-bit. Hebrew simplified that to 22 letters.  
**We use Hebrew externally and 64-bit internally.**

Every sealed answer carries `answer_that_answers.representation`:
- `external.hebrew_stream_22`
- `internal.u64_limbs` / `op_u64_hex`
- per-term dual for SY matches

### Hebrew (limited only)

Hebrew is **not** free modern Hebrew.  
It is **limited Hebrew from Sefer Yetzira (Book of Formations)** — the lexicon aligned with the advanced Creators SY book:

- source book mapping: Sefer Yetzira terms → computer language  
- advanced tree (owner): `/Users/adicohen/work/extension/advanced/SY`  
- shipped lexicon: `src/adico_ai_api/lexicon/sefer_yetzira_limited_he.json` (30 sealed terms)

Example that works:

```text
מים אש אויר
```

→ `sy.lexicon.translate` → each term to its computer-language `to` (input / output / process…)

Unknown Hebrew words (not in the book lexicon) → **no id** (honest miss).

Industry clients still use OpenAI/Ollama/Anthropic **wires**.  
What you put in `content` / `prompt` must be **catalog speech**.

## Law

| | |
|---|---|
| Want **everything** | grow **SY lexicon + ops** from the book · users learn those terms |
| Want an answer **now** | speak a form below or a SY term from the lexicon |
| Unknown speech | **no sealed id** → honest miss |
| Same speech again | **one op answer** from local cache |

```
your words  →  form or SY term  →  id  →  install  →  execute(params)
            →  (answer, answer_that_answers)
```

## A) Limited Hebrew — Book of Formations

```bash
curl -s http://127.0.0.1:8843/v1/talk | python3 -c 'import sys,json;d=json.load(sys.stdin);print(json.dumps(d["hebrew"],ensure_ascii=False,indent=2)[:2000])'
```

Sample terms (full list in lexicon / `/v1/talk`):

| say (Hebrew) | computer language |
|---|---|
| מים | קלט (input) |
| אש | פלט (output) |
| אויר | תהליך ללא סימן |
| יוצר | סימן תהליך בלי סימן |
| הבט | קלט גולמי |
| ראה | הופעת הבחנות בתוך הקלט |
| צפה | קשר ממליך בין חלקים |

Compose several terms in one line; each match is translated.

## B) English tool forms (stage 0.1)

Use these as the message body (examples are the teaching).

### Arithmetic — `op.arith`

```text
17*19
2+2
calc 3*(4+5)
= 10/2
```

Digits and `+ - * / % ( )` only (optional `calc` / `=` prefix).

### Time — `op.time.now`

```text
time
clock
now
what is the time
```

### Date — `op.date.today`

```text
date
today
what is the date
```

### Hash — `op.hash.sha256`

```text
hash <text>
sha256 <text>
hsh <text>
```

### Length — `op.text.len`

```text
len <text>
```

### Reverse — `op.text.reverse`

```text
reverse <text>
```

### Identity — `op.identity`

```text
who are you
what are you
your name
```

### Install marker — `op.catalog.install`

```text
install id <op.id>
install_id <op.id>
```

## Parallel (many requests)

```bash
curl -s http://127.0.0.1:8843/v1/ops/batch \
  -H 'Content-Type: application/json' \
  -d '{"texts":["17*19","len hello","hash x"]}'
```

Or chat with `"texts":[...]` / `"adico_parallel": true`.

## What is not talk

- Multi-lingual free speech — **no**
- Free modern Hebrew outside the SY lexicon — **no**
- Prose without a form / book term — **no id** → miss

## How “everything” arrives

1. Grow the **Book of Formations** lexicon + ops from **advanced/SY** chapters.  
2. Each term/id ships **how to say it**.  
3. Users **learn** limited SY Hebrew + tool forms (`GET /v1/talk`).  
4. Surface grows → **everything**, still deterministic.

Talk little. Speak book term or form. Do much. Compute once.
