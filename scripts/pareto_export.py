#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional


PARETO_INPUT_FIELDS = [
    "source_row_index",
    "run_id",
    "run_dir",
    "dataset_id",
    "dataset_version",
    "dataset_split",
    "model",
    "defense_profile",
    "temperature",
    "top_p",
    "max_tokens",
    "failure_rate",
    "parse_error_rate",
    "u",
    "one_minus_asr",
    "fpr",
    "latency_ms",
    "pareto_eligible",
]


def _f(x: Optional[str]) -> Optional[float]:
    try:
        if x is None:
            return None
        s = str(x).strip()
        if s == "" or s.lower() == "none":
            return None
        return float(s)
    except Exception:
        return None


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, fieldnames: List[str], rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _dominates(a: Dict[str, object], b: Dict[str, object], eps: float = 1e-12) -> bool:
    # Maximize: u, one_minus_asr
    au = float(a["u"])
    bu = float(b["u"])
    ar = float(a["one_minus_asr"])
    br = float(b["one_minus_asr"])

    # Minimize: fpr, latency_ms
    af = float(a["fpr"])
    bf = float(b["fpr"])
    al = float(a["latency_ms"])
    bl = float(b["latency_ms"])

    no_worse = (
        (au >= bu - eps)
        and (ar >= br - eps)
        and (af <= bf + eps)
        and (al <= bl + eps)
    )
    strictly_better = (
        (au > bu + eps)
        or (ar > br + eps)
        or (af < bf - eps)
        or (al < bl - eps)
    )
    return no_worse and strictly_better


def _pareto_front(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for i, cand in enumerate(rows):
        dominated = False
        for j, other in enumerate(rows):
            if i == j:
                continue
            if _dominates(other, cand):
                dominated = True
                break
        if not dominated:
            out.append(cand)
    return out


def _pick_latency(row: Dict[str, str], latency_col: str) -> Optional[float]:
    lat = _f(row.get(latency_col))
    if lat is not None:
        return lat
    # fallback to common alternatives
    for key in ("latency_ms_p95", "latency_ms_p50"):
        if key == latency_col:
            continue
        v = _f(row.get(key))
        if v is not None:
            return v
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Export pareto_input.csv and pareto_points.csv from results_matrix.csv.")
    ap.add_argument("--in", dest="inp", default="results_matrix.csv", help="Input results matrix CSV")
    ap.add_argument("--out-input", default="pareto_input.csv", help="Output path for pareto_input.csv")
    ap.add_argument("--out-points", default="pareto_points.csv", help="Output path for pareto_points.csv")
    ap.add_argument("--u-col", default="u_mean", help="Utility column (maximize)")
    ap.add_argument("--asr-col", default="ASR_strict", help="ASR column; robustness is (1 - ASR)")
    ap.add_argument("--fpr-col", default="FPR_strict", help="FPR column (minimize)")
    ap.add_argument("--latency-col", default="latency_ms_p95", help="Latency column (minimize)")
    args = ap.parse_args()

    rows = _read_csv(Path(args.inp))
    pareto_input_rows: List[Dict[str, object]] = []

    for idx, row in enumerate(rows):
        u = _f(row.get(args.u_col))
        asr = _f(row.get(args.asr_col))
        if asr is None:
            asr = _f(row.get("asr"))
        fpr = _f(row.get(args.fpr_col))
        if fpr is None:
            fpr = _f(row.get("fpr"))
        latency = _pick_latency(row, args.latency_col)
        one_minus_asr = (1.0 - asr) if asr is not None else None
        eligible = (
            u is not None
            and one_minus_asr is not None
            and fpr is not None
            and latency is not None
        )

        pareto_input_rows.append(
            {
                "source_row_index": idx,
                "run_id": row.get("run_id", ""),
                "run_dir": row.get("run_dir", ""),
                "dataset_id": row.get("dataset_id", ""),
                "dataset_version": row.get("dataset_version", ""),
                "dataset_split": row.get("dataset_split", ""),
                "model": row.get("model", ""),
                "defense_profile": row.get("defense_profile") or row.get("defense") or "",
                "temperature": row.get("temperature", ""),
                "top_p": row.get("top_p", ""),
                "max_tokens": row.get("max_tokens", ""),
                "failure_rate": row.get("failure_rate", ""),
                "parse_error_rate": row.get("parse_error_rate", ""),
                "u": u,
                "one_minus_asr": one_minus_asr,
                "fpr": fpr,
                "latency_ms": latency,
                "pareto_eligible": bool(eligible),
            }
        )

    eligible_rows = [r for r in pareto_input_rows if bool(r.get("pareto_eligible"))]
    pareto_points = _pareto_front(eligible_rows)

    # Stable ordering in output.
    pareto_points = sorted(
        pareto_points,
        key=lambda r: (
            -float(r["u"]),
            -float(r["one_minus_asr"]),
            float(r["fpr"]),
            float(r["latency_ms"]),
            str(r.get("run_id", "")),
        ),
    )

    _write_csv(Path(args.out_input), PARETO_INPUT_FIELDS, pareto_input_rows)
    _write_csv(Path(args.out_points), PARETO_INPUT_FIELDS, pareto_points)

    print(f"Wrote {len(pareto_input_rows)} rows -> {args.out_input}")
    print(
        f"Wrote {len(pareto_points)} Pareto points (eligible={len(eligible_rows)}) -> {args.out_points}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
