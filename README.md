# adico-ai-api

**Owner:** כהן עובדיה עדי (adico)  
**Status:** potential → becoming actual (honest: full human-class doer is not claimed done)

Industry-shaped AI API. **Data stays local. Life is on the network.** Many develop it; many use it after.

## Product law

| law | meaning |
|---|---|
| Most complex request | **everything** a human can ask to know or do with the same body + connectivity |
| Today’s industry AI | practically **nothing** complete under that bar |
| This API (potential) | answers **everything in parallel** via sealed ops |
| Deterministic | input → questions-of-question → **id** → **install** → **execute(params)** → **(answer, answer_that_answers)** |
| Waste | talk little, do much · **compute once** · re-ask → **one op answer** (cache hit) |
| Data | **local** per user machine |
| Life | **network**: protocol, catalog of ids, multi-dev, multi-user |

This is **not** a new proprietary chat dialect. Wire shape = what the industry already speaks:

- OpenAI: `POST /v1/chat/completions`, `GET /v1/models`
- Ollama-compatible: `POST /api/chat`, `POST /api/generate`, `GET /api/tags`
- Anthropic-shaped: `POST /v1/messages`

## Quick start (local)

```bash
cd adico-ai-api
python3 -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt                      # none required for stdlib server
./start.sh
# or:
python3 -m adico_ai_api.server
```

Loopback only by default:

```text
http://127.0.0.1:8843/health
http://127.0.0.1:8843/v1/models
```

```bash
curl -s http://127.0.0.1:8843/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"adico-ops","messages":[{"role":"user","content":"17*19"}]}'
```

Dual out is always present on sealed ops:

```json
{
  "answer": "17*19 = 323",
  "answer_that_answers": { "id": "...", "source": "cache|execute", "key": "..." }
}
```

Industry clients still get a single `choices[0].message.content` string; structured dual lives under `adico`.

## Pipeline

```
requests[1..N]
  → translate → id (+ params)
  → install(id) on demand
  → execute(id, params)     # skip if cache hit
  → (answer, answer_that_answers)
  → store key = sha256(canonical(id, params))
re-ask → return stored op only
```

## Layout

```text
src/adico_ai_api/
  server.py      # industry HTTP face (stdlib)
  pipeline.py    # id · install · execute · dual · parallel batch
  cache.py       # local one-op store (jsonl)
  catalog.py     # sealed op ids (extend here / load books later)
  config.py
docs/openapi.yaml
data/            # local cache (gitignored contents)
```

## Network life / local data

- **Local:** cache, ledger optional path, bind `127.0.0.1` by default.
- **Network life:** this repo is the shared contract multi-dev grows; users run the face on their machine and keep their data in `./data`.
- Optional bridge to an existing Adi host process: set `ADICO_UPSTREAM=http://127.0.0.1:8443` to forward freeform after local sealed miss (does not send your cache off-machine).

## Env

| var | default | meaning |
|---|---|---|
| `ADICO_API_HOST` | `127.0.0.1` | bind host |
| `ADICO_API_PORT` | `8843` | bind port |
| `ADICO_DATA` | `./data` | local cache dir |
| `ADICO_UPSTREAM` | empty | optional local upstream for freeform |
| `ADICO_ALLOW_NON_LOOPBACK` | `0` | must be `1` to bind non-loopback |

## Honesty

- **Potential:** everything in parallel, books → ids, human-body class do.
- **Actual in this repo today:** industry face + sealed catalog ops + install/execute hooks + **one-op local cache** + dual out + batch parallel execute for multiple user messages.
- Extending the catalog (from symbolic books) is how potential becomes act — not chat agreement.

## Owner

כהן עובדיה עדי · adico · adico1
