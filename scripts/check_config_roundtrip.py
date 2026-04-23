#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench.core.config import RunConfig


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate config roundtrip and defense field preservation.")
    ap.add_argument("--config", required=True, help="Path to YAML/JSON run config")
    ap.add_argument(
        "--out-json",
        default=None,
        help="Optional path to write serialized config JSON (for inspection)",
    )
    args = ap.parse_args()

    cfg_path = Path(args.config)
    raw_obj = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) if cfg_path.suffix in {".yaml", ".yml"} else json.loads(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(raw_obj, dict):
        print("Config root must be a mapping", file=sys.stderr)
        return 2

    cfg = RunConfig.load(cfg_path)
    payload = cfg.model_dump(mode="json", exclude_none=False)

    raw_defense = raw_obj.get("defense") or {}
    if not isinstance(raw_defense, dict):
        raw_defense = {}
    dumped_defense = payload.get("defense") or {}
    if not isinstance(dumped_defense, dict):
        dumped_defense = {}

    missing = sorted(k for k in raw_defense.keys() if k not in dumped_defense)
    if missing:
        print("Missing defense keys after roundtrip:", ", ".join(missing), file=sys.stderr)
        return 1

    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "config": str(cfg_path),
                "defense_keys_in_input": sorted(raw_defense.keys()),
                "defense_keys_in_output": sorted(dumped_defense.keys()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
