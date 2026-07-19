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

from . import bits64, cache, catalog, config, cosmos, ledger
from . import PRODUCT_ID, PRODUCT_NAME, COMPANY, OWNER


def _attach_dual(ata: dict, text: str, op_id: str, params: dict) -> dict:
    """Hebrew external · 64-bit internal on every sealed result."""
    matches = None
    if op_id == "sy.lexicon.translate" and isinstance(params, dict):
        matches = params.get("matches")
    ata["representation"] = bits64.dual_rep(
        external=text,
        op_id=op_id,
        params=params,
        matches=matches,
    )
    return ata


def _bind_cosmos(
    *,
    user: str | None,
    op_id: str,
    params: dict,
    raw_input: str,
    machine_answer: str,
    ata: dict,
) -> tuple[str, dict]:
    """
    Every function: compute cosmos address from input → request exists or register;
    address-about-address; Hebrew answer.
    """
    c = cosmos.resolve_request(
        user=user,
        op_id=op_id,
        params=params,
        raw_input=raw_input,
        machine_answer=machine_answer,
    )
    ata["cosmos"] = c
    block = cosmos.format_cosmos_block(c)
    # machine answer first, then cosmos + Hebrew
    full = f"{machine_answer}\n\n{block}"
    return full, c


def run_one(text: str, mi: str | None = None) -> dict[str, Any]:
    """Full pipe for one user text. Never invents sealed answer if no id.

    mi = asking user id (perspective for cosmos unique address).
    """
    user = (mi or "").strip() or None
    translated = catalog.translate(text)
    if translated is None:
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
                "representation": bits64.dual_rep(external=text or ""),
            },
            "text": (
                f"{PRODUCT_NAME}: no_sy_word. "
                "Speech=SY lexicon words only. Target=programming terms only. "
                "No free Hebrew. No mysticism. Learn words: GET /v1/talk."
            ),
        }

    op_id = translated["id"]
    params = dict(translated["params"] or {})
    qoq = translated["question_of_question"]

    def _clean(p: dict) -> dict:
        return {k: v for k, v in (p or {}).items() if not str(k).startswith("_")}

    params_key = _clean(params)
    # cosmos address is part of uniqueness: same op+params+user
    key_preview = cache.canonical_key(
        op_id, {**params_key, "_user": user or "anonymous_local"}
    )

    # ── on-demand id decider: MEASURE FIRST ──
    hit = cache.get(
        config.CACHE_PATH, op_id, {**params_key, "_user": user or "anonymous_local"}
    )
    if hit is not None:
        ledger.measure_first(op_id, params_key, cache_hit=True, key=hit.get("key"))
        ata = dict(hit.get("answer_that_answers") or {})
        ata["source"] = "cache"
        ata["key"] = hit["key"]
        ata["reused"] = True
        ata["decider"] = "measure_first → cache_hit (no re-install, no re-execute)"
        _attach_dual(ata, qoq, op_id, params_key)
        return {
            "ok": True,
            "sealed": True,
            "id": op_id,
            "params": params_key,
            "question_of_question": qoq,
            "answer": hit["answer"],
            "answer_that_answers": ata,
            "text": hit["answer"],
            "cache": "hit",
            "key": hit["key"],
            "decider": "measure_first_cache_hit",
            "cosmos": ata.get("cosmos"),
            "hebrew_answer": (ata.get("cosmos") or {}).get("hebrew_answer"),
            "internal_op_u64_hex": ata["representation"]["internal"].get("op_u64_hex"),
        }

    # ── measure: must install and execute ──
    ledger.measure_first(op_id, params_key, cache_hit=False, key=key_preview)
    inst = catalog.install(op_id)
    sig_i = ledger.install_event(op_id, inst)
    if not inst.get("installed"):
        return {
            "ok": False,
            "sealed": True,
            "id": op_id,
            "answer": None,
            "answer_that_answers": {
                "status": "install_failed",
                "install": inst,
                "decider": "measure_first → install_failed",
                "ledger_install_sig": sig_i,
            },
            "text": f"op id={op_id} not installed",
        }

    machine = catalog.execute(op_id, params)
    key = key_preview
    extra = {}
    if op_id == "op.address.sum" and isinstance(params.get("_address_result"), dict):
        extra["address"] = {
            "mode": params["_address_result"].get("mode"),
            "address_hex": params["_address_result"].get("address_hex"),
        }
    sig_e = ledger.execute_event(op_id, key, len(machine or ""), extra=extra or None)
    ata = {
        "status": "executed",
        "id": op_id,
        "params": params_key,
        "question_of_question": qoq,
        "install": inst,
        "source": "execute",
        "key": key,
        "reused": False,
        "owner": OWNER,
        "company": COMPANY,
        "product": PRODUCT_ID,
        "decider": "measure_first → install → execute → cosmos_address",
        "ledger": {"install_sig": sig_i, "execute_sig": sig_e},
        "law": (
            "each function → cosmos address from input; "
            "request existing or register; "
            "address-about-address; Hebrew answer"
        ),
    }
    answer, c = _bind_cosmos(
        user=user,
        op_id=op_id,
        params=params_key,
        raw_input=qoq,
        machine_answer=machine,
        ata=ata,
    )
    _attach_dual(ata, qoq, op_id, params_key)
    rec = cache.put(
        config.CACHE_PATH,
        op_id,
        {**params_key, "_user": user or "anonymous_local"},
        answer,
        ata,
    )
    return {
        "ok": True,
        "sealed": True,
        "id": op_id,
        "params": params_key,
        "question_of_question": qoq,
        "answer": answer,
        "answer_that_answers": ata,
        "text": answer,
        "cache": "miss",
        "key": rec["key"],
        "decider": "install_and_execute",
        "cosmos": c,
        "hebrew_answer": c.get("hebrew_answer"),
        "internal_op_u64_hex": ata["representation"]["internal"].get("op_u64_hex"),
    }


def run_many(
    texts: list[str], max_workers: int = 8, mi: str | None = None
) -> list[dict[str, Any]]:
    """Parallel potential: N requests → N ops at once."""
    if not texts:
        return []
    if len(texts) == 1:
        return [run_one(texts[0], mi=mi)]
    out: list[dict[str, Any] | None] = [None] * len(texts)
    with ThreadPoolExecutor(max_workers=min(max_workers, len(texts))) as pool:
        futs = {pool.submit(run_one, t, mi): i for i, t in enumerate(texts)}
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
    """Industry message.content — machine + cosmos + Hebrew when sealed."""
    ans = result.get("answer") if result.get("answer") is not None else result.get("text")
    ata = result.get("answer_that_answers") or {}
    if result.get("sealed") and result.get("ok"):
        # answer already includes cosmos block on execute; cache hits too
        return str(ans or "")
    if ans:
        return str(ans)
    return str(result.get("text") or json.dumps(ata, ensure_ascii=False))
