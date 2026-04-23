#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import random
import sys
from typing import Any, Dict, List, Optional


def read_cases(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def _clip_text(value: Any, max_chars: int) -> str:
    if value is None:
        return ""
    s = str(value).replace("\r", " ").replace("\n", " ").strip()
    if len(s) <= max_chars:
        return s
    if max_chars <= 1:
        return s[:max_chars]
    return s[: max_chars - 1] + "…"


def _row_status(row: Dict[str, Any]) -> str:
    status = row.get("status")
    if not isinstance(status, str) or not status.strip():
        return "ok"
    return status.strip()


def _join_signals(row: Dict[str, Any]) -> str:
    signals = row.get("refusal_signals")
    if isinstance(signals, list):
        return " | ".join(str(x) for x in signals)
    if signals is None:
        return ""
    return str(signals)


def _raw_text(row: Dict[str, Any]) -> str:
    return str(row.get("raw_text") or row.get("response_text") or "")


def _final_text(row: Dict[str, Any]) -> str:
    return str(row.get("final_text") or row.get("response_text") or row.get("raw_text") or "")


def _project_row(row: Dict[str, Any], *, max_chars: int) -> Dict[str, Any]:
    return {
        "case_id": row.get("case_id"),
        "case_type": row.get("case_type"),
        "category": row.get("category"),
        "family_id": row.get("family_id"),
        "status": _row_status(row),
        "expected_action": row.get("expected_action"),
        "predicted_action": row.get("predicted_action"),
        "goal_hit": row.get("goal_hit"),
        "refusal_signals": _clip_text(_join_signals(row), max_chars),
        "raw_text": _clip_text(_raw_text(row), max_chars),
        "final_text": _clip_text(_final_text(row), max_chars),
    }


def _to_markdown(rows: List[Dict[str, Any]]) -> str:
    headers = [
        "case_id",
        "case_type",
        "category",
        "family_id",
        "status",
        "expected_action",
        "predicted_action",
        "goal_hit",
        "refusal_signals",
        "raw_text",
        "final_text",
    ]

    def esc(v: Any) -> str:
        s = "" if v is None else str(v)
        return s.replace("|", "\\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(esc(row.get(h)) for h in headers) + " |")
    return "\n".join(lines) + "\n"


def _to_csv(rows: List[Dict[str, Any]], out_path: Path) -> None:
    fieldnames = list(rows[0].keys()) if rows else [
        "case_id",
        "case_type",
        "category",
        "family_id",
        "status",
        "expected_action",
        "predicted_action",
        "refusal_signals",
        "goal_hit",
        "raw_text",
        "final_text",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def main() -> int:
    ap = argparse.ArgumentParser(description="Sample and export a small manual-audit sheet from cases.jsonl")
    ap.add_argument("--cases", default=None, help="Path to cases.jsonl")
    ap.add_argument("--run-dir", default=None, help="Run directory containing cases.jsonl")
    ap.add_argument("-n", "--sample-size", type=int, default=30, help="Number of rows to sample")
    ap.add_argument("--seed", type=int, default=42, help="Random seed")
    ap.add_argument("--only", choices=["attack", "benign", "utility"], default=None, help="Filter by case type")
    ap.add_argument(
        "--case-type",
        choices=["attack", "benign", "utility"],
        default=None,
        help="Deprecated alias for --only",
    )
    ap.add_argument(
        "--status",
        default=None,
        help="Filter by status (for example: ok, timeout, http_error, parse_error)",
    )
    ap.add_argument("--max-chars", type=int, default=240, help="Max chars for text fields (raw/final/signals)")
    ap.add_argument("--format", choices=["md", "csv"], default="md")
    ap.add_argument("--out", default=None, help="Output path (stdout if omitted for md)")
    args = ap.parse_args()

    if args.cases and args.run_dir:
        print("Provide only one of --cases or --run-dir.", file=sys.stderr)
        return 2
    if not args.cases and not args.run_dir:
        print("One of --cases or --run-dir is required.", file=sys.stderr)
        return 2

    cases_path: Optional[Path] = None
    if args.cases:
        cases_path = Path(args.cases)
    elif args.run_dir:
        cases_path = Path(args.run_dir) / "cases.jsonl"

    if cases_path is None or not cases_path.exists():
        print(f"cases.jsonl not found: {cases_path}", file=sys.stderr)
        return 2

    rows = read_cases(cases_path)
    selected_type = args.only or args.case_type
    if selected_type:
        rows = [r for r in rows if r.get("case_type") == selected_type]
    if args.status:
        status_filter = str(args.status).strip()
        rows = [r for r in rows if _row_status(r) == status_filter]
    if not rows:
        print("No rows matched the filter.", file=sys.stderr)
        return 1

    rng = random.Random(args.seed)
    k = min(max(args.sample_size, 1), len(rows))
    sampled = rng.sample(rows, k=k)
    projected = [_project_row(r, max_chars=max(args.max_chars, 16)) for r in sampled]

    if args.format == "md":
        md = _to_markdown(projected)
        if args.out:
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(md, encoding="utf-8")
            print(f"Wrote {len(projected)} rows -> {out}")
        else:
            sys.stdout.write(md)
        return 0

    out = Path(args.out or "audit_sample.csv")
    _to_csv(projected, out)
    print(f"Wrote {len(projected)} rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
