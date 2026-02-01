#!/usr/bin/env python3
"""Merge multiple dataset files (YAML list or JSONL) into one JSONL.

Example:
  python scripts/merge_datasets.py \
    --out data/merged_safety_utility.jsonl \
    data/safety/benign_mvp_115.yaml data/utility/utility_ru_mvp.jsonl

The runner accepts YAML or JSONL, but JSONL is the easiest common format.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml


def load_any(p: Path) -> List[Dict[str, Any]]:
    suf = p.suffix.lower()
    if suf in {".yaml", ".yml"}:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"YAML must be a list of cases: {p}")
        return list(data)
    if suf == ".jsonl":
        out = []
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out
    raise ValueError(f"Unsupported format: {p}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    merged: List[Dict[str, Any]] = []
    seen = set()

    for p in args.paths:
        for obj in load_any(p):
            cid = str(obj.get("id"))
            if cid in seen:
                # Make it unique but stable
                k = 2
                while f"{cid}__{k}" in seen:
                    k += 1
                obj = dict(obj)
                obj["id"] = f"{cid}__{k}"
                cid = obj["id"]
            seen.add(cid)
            merged.append(obj)

    out = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for obj in merged:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print(json.dumps({"out": str(out), "n": len(merged)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
