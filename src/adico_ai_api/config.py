from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOST = os.environ.get("ADICO_API_HOST", "127.0.0.1")
PORT = int(os.environ.get("ADICO_API_PORT", "8843"))
DATA = Path(os.environ.get("ADICO_DATA", str(ROOT / "data"))).expanduser().resolve()
CACHE_PATH = DATA / "ops_cache.jsonl"
CATALOG_EXTRA = Path(os.environ.get("ADICO_CATALOG", str(DATA / "catalog_extra.json")))
UPSTREAM = os.environ.get("ADICO_UPSTREAM", "").rstrip("/")
ALLOW_NON_LOOPBACK = os.environ.get("ADICO_ALLOW_NON_LOOPBACK", "0") in ("1", "true", "True")
EXECUTE_TIMEOUT = float(os.environ.get("ADICO_EXECUTE_TIMEOUT_SEC", "120"))

DATA.mkdir(parents=True, exist_ok=True)
