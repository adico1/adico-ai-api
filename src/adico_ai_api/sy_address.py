"""
SY addressing (Book of Formations) — not SHA-cosmos lottery.

  · 22 otiyot (letters)
  · 231 gates = C(22,2) = 22×21/2  (two-letter combinations)
  · 32 netivot (paths) — routing / address bus

Law (Adi):
  The unique name of a thing IS its cosmic address.
  As language evolves, new names are created to identify new things.
  That name-growth is the infinite · infinite · infinity of address space.
  22·231·32 is the finite engine of naming; speech/lexicon growth is open.

Uniqueness = identity under the unified SY language + geometry:
  same name/seal ⇒ same address ⇒ same thing.
  new thing ⇒ new name (lexicon/compound) ⇒ new address.

64-bit internal = packed discrete SY seal (machine face).
Hebrew external = name face of the seal (22-letter stream).
"""
from __future__ import annotations

import json
from typing import Any

from . import bits64

OTIYOT_22 = bits64.OTIYOT_22
N_LETTERS = 22
N_GATES = N_LETTERS * (N_LETTERS - 1) // 2  # 231
N_NETIVOT = 32  # שלשים ושתים נתיבות
MASK64 = bits64.MASK64

assert N_GATES == 231


def letter_index(ch: str) -> int | None:
    return bits64.letter_index(ch)


def gate_index(i: int, j: int) -> int:
    """Unordered pair (i,j), i≠j → 0..230."""
    if i == j:
        raise ValueError("gate needs two distinct letters")
    if i > j:
        i, j = j, i
    # pairs with first index < i, then offset in row
    return i * (2 * N_LETTERS - i - 1) // 2 + (j - i - 1)


def gate_letters(g: int) -> tuple[int, int]:
    """Inverse of gate_index → (i,j) with i<j."""
    if not (0 <= g < N_GATES):
        raise ValueError("gate out of range")
    # find i such that gate_index(i, i+1) <= g < gate_index(i+1, i+2) row start
    for i in range(N_LETTERS - 1):
        row_len = N_LETTERS - 1 - i
        row_start = i * (2 * N_LETTERS - i - 1) // 2
        if g < row_start + row_len:
            j = i + 1 + (g - row_start)
            return i, j
    raise ValueError("gate decode failed")


def letters_from_text(text: str) -> list[int]:
    stream = bits64.normalize_hebrew(text or "")
    out = []
    for ch in stream:
        idx = letter_index(ch)
        if idx is not None:
            out.append(idx)
    return out


def gates_from_letters(idxs: list[int]) -> list[int]:
    """
    Gates along the stream: each consecutive distinct pair.
    Also include sorted unique combination pairs present (for seal richness).
    """
    gates: list[int] = []
    seen = set()
    for a, b in zip(idxs, idxs[1:]):
        if a == b:
            continue
        g = gate_index(a, b)
        gates.append(g)
        seen.add(g)
    # all unique unordered pairs appearing in multiset of letters
    uniq = sorted(set(idxs))
    for ii in range(len(uniq)):
        for jj in range(ii + 1, len(uniq)):
            g = gate_index(uniq[ii], uniq[jj])
            if g not in seen:
                gates.append(g)
                seen.add(g)
    return gates


def netiv_from_seal(letter_idxs: list[int], gate_ids: list[int], salt: str = "") -> int:
    """
    Path 0..31 — discrete routing slot on the 32-path bus.
    Derived only from SY seal material + short salt (op/user tags as letters if any).
    No SHA. Fold with builtin ops only.
    """
    import operator as op

    acc = 0
    for i, li in enumerate(letter_idxs or [0]):
        acc = op.add(acc, op.mul(li + 1, i + 1))
    for g in gate_ids or [0]:
        acc = op.add(acc, g + 1)
    for ch in bits64.normalize_hebrew(salt):
        li = letter_index(ch)
        if li is not None:
            acc = op.add(acc, li + 1)
    # map into 32 paths
    return acc % N_NETIVOT


def pack_seal_u64(netiv: int, letter_idxs: list[int], gate_ids: list[int]) -> int:
    """
    Pack discrete SY seal into one u64 machine face:
      bits [0:5)   netiv (5 bits enough for 32)
      bits [5:13)  letter count (capped)
      remaining    mix of letters and gates via base folds (operator only)
    """
    import operator as op

    netiv = int(netiv) % N_NETIVOT
    v = netiv & 0x1F
    # fold letters
    for li in letter_idxs[:24]:
        v = op.mul(v, N_LETTERS)
        v = op.add(v, li)
        v &= MASK64
    # fold gates
    for g in gate_ids[:16]:
        v = op.mul(v, N_GATES)
        v = op.add(v, g)
        v &= MASK64
    # keep netiv recoverable in low bits: re-embed
    v = ((v >> 5) << 5) | (netiv & 0x1F)
    return v & MASK64


def seal_hebrew(netiv: int, letter_idxs: list[int], gate_ids: list[int]) -> str:
    """External Hebrew face of the seal (22 letters only)."""
    chars = []
    # encode netiv as two letters (base 22)
    chars.append(OTIYOT_22[netiv % N_LETTERS])
    chars.append(OTIYOT_22[(netiv // N_LETTERS) % N_LETTERS])
    for li in letter_idxs[:20]:
        chars.append(OTIYOT_22[li % N_LETTERS])
    # mark gates as letter pairs (first of each gate only to bound length)
    for g in gate_ids[:10]:
        i, j = gate_letters(g)
        chars.append(OTIYOT_22[i])
        chars.append(OTIYOT_22[j])
    return "".join(chars) if chars else OTIYOT_22[0]


def about_seal(parent_u64: int, parent_he: str, netiv: int) -> dict[str, Any]:
    """
    Address about address: new seal from parent Hebrew + parent netiv gate material.
    Still SY-only (letters/gates/path), no SHA.
    """
    idxs = letters_from_text(parent_he)
    if not idxs:
        idxs = [parent_u64 % N_LETTERS, (parent_u64 // N_LETTERS) % N_LETTERS]
    gates = gates_from_letters(idxs)
    # path offset from parent
    n2 = (netiv + 1 + (parent_u64 % N_NETIVOT)) % N_NETIVOT
    if not gates and len(idxs) >= 2:
        gates = [gate_index(idxs[0], idxs[1])]
    elif not gates:
        gates = [gate_index(0, 1 + (n2 % 20))]
    u = pack_seal_u64(n2, idxs, gates)
    he = seal_hebrew(n2, idxs, gates)
    return {
        "netiv": n2,
        "letters": idxs,
        "gates": gates,
        "u64": u,
        "hex": f"{u:016x}",
        "hebrew": he,
    }


def build_sy_address(
    *,
    raw_input: str,
    op_id: str,
    params: dict,
    user: str | None,
) -> dict[str, Any]:
    """
    Full SY address for a request under unified language.
    Material: input letters (+ op_id/user mapped only via Hebrew letters present).
    """
    # primary letter stream from human/SY input
    salt_he = bits64.normalize_hebrew((user or "") + (op_id or ""))
    idxs = letters_from_text(raw_input)
    if not idxs:
        # machine ops with no Hebrew: derive letters from op_id digits/hex not Latin —
        # use fixed empty path material from params digest via letter indices of length only
        # Prefer: take any SY words inside op_id path — else use netiv-only seal from param sizes
        idxs = []
        blob = json.dumps(params or {}, ensure_ascii=False, sort_keys=True, default=str)
        # map each char that is Hebrew; else use length-mod letters (not SHA)
        for ch in blob:
            li = letter_index(ch) if ch in OTIYOT_22 or ch in "ךםןףץ" else None
            if li is not None:
                idxs.append(li)
        if not idxs:
            n = (len(blob) + len(op_id or "") + len(user or "")) % N_LETTERS
            idxs = [n, (n * 3 + 1) % N_LETTERS, (n * 5 + 2) % N_LETTERS]

    gates = gates_from_letters(idxs)
    netiv = netiv_from_seal(idxs, gates, salt=salt_he + bits64.normalize_hebrew(raw_input))
    u64 = pack_seal_u64(netiv, idxs, gates)
    he = seal_hebrew(netiv, idxs, gates)

    about = about_seal(u64, he, netiv)
    about2 = about_seal(about["u64"], about["hebrew"], about["netiv"])

    return {
        "scheme": "sy_32_paths_22_letters_231_gates",
        "geometry": {
            "netivot": N_NETIVOT,
            "otiyot": N_LETTERS,
            "gates": N_GATES,
        },
        "thing": {
            "netiv": netiv,
            "letters": idxs,
            "gates": gates,
            "gate_count": len(gates),
            "address_u64": u64,
            "address_hex": f"{u64:016x}",
            "hebrew": he,
            "role": "sy_seal_of_the_thing",
        },
        "about_thing": {
            "netiv": about["netiv"],
            "letters": about["letters"],
            "gates": about["gates"],
            "address_u64": about["u64"],
            "address_hex": about["hex"],
            "hebrew": about["hebrew"],
            "role": "sy_seal_about_seal",
        },
        "about_about": {
            "netiv": about2["netiv"],
            "letters": about2["letters"],
            "gates": about2["gates"],
            "address_u64": about2["u64"],
            "address_hex": about2["hex"],
            "hebrew": about2["hebrew"],
            "role": "sy_seal_about_seal_about_seal",
        },
        "law": (
            "unique name of a thing = its cosmic address; "
            "22+231+32 = naming engine; "
            "language evolves → new names → new addresses → infinite infinite infinity; "
            "not SHA lottery"
        ),
        "name": he,
        "name_is_address": True,
    }
