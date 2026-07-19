# How to talk to adico-ops (this stage)

**Not multi-lingual yet.**  
There is one speech surface: **sealed forms** that translate to **ids**.  
People must **learn this speech** in order to request work. Free chat is not the product.

Industry clients still use OpenAI/Ollama/Anthropic **wires**.  
What you put in `content` / `prompt` must be **catalog speech**, not natural-language everything.

## Law

| | |
|---|---|
| Want **everything** | grow the **catalog of ids** + learn more speech forms |
| Want an answer **now** | speak a form below exactly (or close regex) |
| Unknown speech | **no sealed id** → honest miss (no invention) |
| Same speech again | **one op answer** from local cache |

```
your words  →  must match a form  →  id  →  install  →  execute(params)
            →  (answer, answer_that_answers)
```

## Speech forms (stage 0.1)

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

## What is not talk (yet)

- Multi-lingual free speech (any human language) — **not yet**
- “Do everything I mean in prose” without a form — **no id** → miss
- Re-phrasing the same ask in novel words hoping for magic — learn the form or add an id

## How “everything” arrives

1. Developers add **ids** (from books / specs / code) to the catalog.  
2. Each id ships a **speech form** (how people must talk).  
3. Users **learn the forms** (this file + `GET /v1/talk`).  
4. Request surface grows → toward **everything**, still deterministic.

Talk little. Speak form. Do much. Compute once.
