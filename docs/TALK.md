# How to talk (HE API)

## Law

| | |
|---|---|
| **Speech** | **SY words only** (Sefer Yetzira / Book of Formations lexicon) |
| **Target** | **programming / computer terms only** |
| **Mysticism** | **none** — no mystic gloss in answers |
| **Multi-lingual** | **no** |
| **Internal** | 64-bit |
| **Spaces / punct** | allowed in the stream |

```
SY word(s)  →  programming term(s)  →  u64
```

People **learn the SY word list**. Unknown words → `no_sy_word`.

## Core I/O example

```text
מים אש ואויר
```

```text
programming:
  input -> output -> process

sy_word -> programming_term:
  מים = input
  אש = output
  אויר = process
```

## Full map (stage lexicon)

| SY word | programming term |
|---|---|
| מים | input |
| אש | output |
| אויר | process |
| יוצר | process_tag |
| למכונו | bind_symbol |
| אות בשם | named_control |
| ממיר_אינם_לישנם | complete_or_fix |
| 1 ראשית | loop |
| 2 אחרית | open_exit |
| 3 טוב | commit |
| 4 רע | struct |
| 5 רום | schema_top |
| 6 תחת | data_base |
| 7 מזרח | channel_head |
| 8 מערב | history_log |
| 9 צפון | unsealed |
| 10 דרום | auth |
| עומק מערב | history_back |
| עומק אחרית | sealed_outbox |
| צפה | link |
| הבט | raw_input |
| ראה | parse |
| צר | reduce |
| שוכנים | runtime_agents |
| 7 עדים | witness_set |

`ו` prefix = and (e.g. `ואויר` → process).

Live list: `GET /v1/talk` → `sy.lexicon`.

## Not supported as speech

- Free modern Hebrew outside the list  
- Mystic / religious explanation as the answer  
- English prose as the HE language  

## Machine op: `sum` = address

Not SY speech. Not mystic. **Address op:**

| mode | meaning |
|---|---|
| `request_existing` | address already registered — return it |
| `tune_calculate` | calculate address from parts, register it |

```text
sum מים אש אויר
sum input output process
sum 0x10a5b 0x14
sum(1, 2, 3)
```

Address = Σ part.u64 (mod 2^64).  
Parts = SY words · programming terms · explicit u64.

Other machine ops (`hash`, arith, …) stay under `machine_ops_not_sy`.

## Wire

Industry HTTP still: `POST /v1/chat/completions` with SY words in `content`.
