from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

from bench.core.config import RunConfig
from bench.core.storage import config_hash_sha256, utc_now_iso


class ResponseCache:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def key(self, run_cfg: RunConfig, case_id: str, repeat: int) -> str:
        raw = f"{config_hash_sha256(run_cfg)}::{case_id}::{int(repeat)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _path_for_key(self, key: str) -> Path:
        shard = key[:2]
        d = self.cache_dir / shard
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{key}.json"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        p = self._path_for_key(key)
        if not p.exists():
            return None
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
        return obj if isinstance(obj, dict) else None

    def put(self, key: str, payload: Dict[str, Any]) -> None:
        p = self._path_for_key(key)
        data: Dict[str, Any] = dict(payload)
        data.setdefault("timestamp", utc_now_iso())
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
