"""Load secrets/.env (or .env) into os.environ. Real env vars always win."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = (ROOT / "secrets" / ".env", ROOT / ".env")
_loaded = False


def load_env(force: bool = False) -> None:
    global _loaded
    if _loaded and not force:
        return
    for path in CANDIDATES:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)
    _loaded = True
