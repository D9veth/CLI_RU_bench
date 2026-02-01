#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from bench.core.dataset import load_dataset, Case


def case_to_obj(c: Case) -> dict:
    obj = {
        "id": c.case_id,
        "type": c.case_type,
        "category": c.category,
        "family_id": c.family_id,
        "scenario": c.scenario,
        "expected_action": c.expected_action,
        "messages": [{"role": m.role, "content": m.content} for m in c.messages],
    }
    if c.goal_indicators:
        obj["goal_indicators"] = c.goal_indicators
    if c.utility_task:
        obj["utility_task"] = c.utility_task
    if c.reference:
        obj["reference"] = c.reference
    if c.meta:
        obj["meta"] = c.meta
    return obj


def main():
    ap = argparse.ArgumentParser(description="Create a stratified pilot subset from a merged dataset.")
    ap.add_argument("--in", dest="inp", required=True, help="Input dataset (.yaml/.jsonl)")
    ap.add_argument("--out", dest="out", required=True, help="Output JSONL path")
    ap.add_argument("--attacks", type=int, default=32, help="Number of attack cases")
    ap.add_argument("--benign", type=int, default=32, help="Number of benign cases")
    ap.add_argument("--utility", type=int, default=64, help="Number of utility cases")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    cases = load_dataset(Path(args.inp))
    attacks = [c for c in cases if c.case_type == "attack"]
    benign = [c for c in cases if c.case_type == "benign"]
    utility = [c for c in cases if c.case_type == "utility"]

    def samp(xs, n):
        if not xs or n <= 0:
            return []
        if n >= len(xs):
            return list(xs)
        return random.sample(xs, n)

    picked = samp(attacks, args.attacks) + samp(benign, args.benign) + samp(utility, args.utility)
    random.shuffle(picked)

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8") as f:
        for c in picked:
            f.write(json.dumps(case_to_obj(c), ensure_ascii=False) + "\n")

    print(f"Wrote {len(picked)} cases to {outp}")


if __name__ == "__main__":
    main()
