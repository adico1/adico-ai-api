"""
Deterministic pipeline (product law):

  input → questions-of-question → id → install → execute(params)
       → (answer, answer_that_answers)
       → store; re-ask → one op answer

Parallel: many inputs → many ops concurrently (thread pool).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from . import cache, catalog, config
from . import PRODUCT_ID, PRODUCT_NAME, COMPANY, OWNER


def run_one(text: str) -> dict[str, Any]:
    """Full pipe for one user text. Never invents sealed answer if no id."""
    translated = catalog.translate(text)
    if translated is None:
        # freeform: optional local upstream only (same machine), else honest miss
        free = _freeform_upstream(text)
        if free is not None:
            return free
        return {
            "ok": False,
            "sealed": False,
            "answer": None,
            "answer_that_answers": {
                "status": "no_sealed_id",
                "reason": "input did not translate to a catalog id — no invention",
                "owner": OWNER,
                "product": PRODUCT_ID,
            },
            "text": (
                f"{PRODUCT_NAME}: no sealed id — not multi-lingual yet. "
                "Learn sealed speech: GET /v1/talk or docs/TALK.md. "
                "Speak a catalog form to request an op. "
                "Everything grows by new ids + forms, not free prose."
            ),
        }

    op_id = translated["id"]
    params = translated["params"]
    qoq = translated["question_of_question"]

    # cache first — compute once
    hit = cache.get(config.CACHE_PATH, op_id, params)
    if hit is not None:
        ata = dict(hit.get("answer_that_answers") or {})
        ata["source"] = "cache"
        ata["key"] = hit["key"]
        ata["reused"] = True
        return {
            "ok": True,
            "sealed": True,
            "id": op_id,
            "params": params,
            "question_of_question": qoq,
            "answer": hit["answer"],
            "answer_that_answers": ata,
            "text": hit["answer"],
            "cache": "hit",
            "key": hit["key"],
        }

    inst = catalog.install(op_id)
    if not inst.get("installed"):
        return {
            "ok": False,
            "sealed": True,
            "id": op_id,
            "answer": None,
            "answer_that_answers": {"status": "install_failed", "install": inst},
            "text": f"op id={op_id} not installed",
        }

    answer = catalog.execute(op_id, params)
    key = cache.canonical_key(op_id, params)
    ata = {
        "status": "executed",
        "id": op_id,
        "params": params,
        "question_of_question": qoq,
        "install": inst,
        "source": "execute",
        "key": key,
        "reused": False,
        "owner": OWNER,
        "company": COMPANY,
        "product": PRODUCT_ID,
        "law": "compute_once · re-ask returns this op",
    }
    rec = cache.put(config.CACHE_PATH, op_id, params, answer, ata)
    return {
        "ok": True,
        "sealed": True,
        "id": op_id,
        "params": params,
        "question_of_question": qoq,
        "answer": answer,
        "answer_that_answers": ata,
        "text": answer,
        "cache": "miss",
        "key": rec["key"],
    }


def run_many(texts: list[str], max_workers: int = 8) -> list[dict[str, Any]]:
    """Parallel potential: N requests → N ops at once."""
    if not texts:
        return []
    if len(texts) == 1:
        return [run_one(texts[0])]
    out: list[dict[str, Any] | None] = [None] * len(texts)
    with ThreadPoolExecutor(max_workers=min(max_workers, len(texts))) as pool:
        futs = {pool.submit(run_one, t): i for i, t in enumerate(texts)}
        for fut in as_completed(futs):
            i = futs[fut]
            try:
                out[i] = fut.result()
            except Exception as e:
                out[i] = {
                    "ok": False,
                    "text": f"error={e!r}",
                    "answer": None,
                    "answer_that_answers": {"status": "error", "err": repr(e)[:300]},
                }
    return [x if x is not None else {"ok": False, "text": "empty"} for x in out]


def _freeform_upstream(text: str) -> dict[str, Any] | None:
    base = config.UPSTREAM
    if not base:
        return None
    # only loopback upstreams allowed
    if "127.0.0.1" not in base and "localhost" not in base:
        return None
    body = json.dumps(
        {
            "model": "ka-el-kloud",
            "messages": [{"role": "user", "content": text}],
            "max_tokens": 1024,
            "stream": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        base + "/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=config.EXECUTE_TIMEOUT) as r:
            obj = json.loads(r.read().decode("utf-8"))
        content = (
            ((obj.get("choices") or [{}])[0].get("message") or {}).get("content")
            or ""
        )
        return {
            "ok": True,
            "sealed": False,
            "answer": content,
            "answer_that_answers": {
                "status": "upstream_local",
                "upstream": base,
                "note": "not sealed catalog — freeform bridge only",
            },
            "text": content,
            "cache": "bypass",
        }
    except Exception as e:
        return {
            "ok": False,
            "sealed": False,
            "answer": None,
            "answer_that_answers": {"status": "upstream_error", "err": repr(e)[:200]},
            "text": f"upstream_error={e!r}",
        }


def format_user_visible(result: dict) -> str:
    """Single string for industry message.content — includes dual out briefly."""
    ans = result.get("answer") if result.get("answer") is not None else result.get("text")
    ata = result.get("answer_that_answers") or {}
    if result.get("sealed") and result.get("ok"):
        src = ata.get("source", "?")
        key16 = (ata.get("key") or result.get("key") or "")[:16]
        return f"{ans}\n\n—\nanswer_that_answers: id={result.get('id')} source={src} key={key16}…"
    if ans:
        return str(ans)
    return str(result.get("text") or json.dumps(ata, ensure_ascii=False))
