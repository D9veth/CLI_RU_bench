#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional


def _f(x: Optional[str]) -> Optional[float]:
    try:
        if x is None:
            return None
        s = str(x).strip()
        if not s or s.lower() == "none":
            return None
        return float(s)
    except Exception:
        return None


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _pick(row: Dict[str, str], *keys: str) -> Optional[float]:
    for k in keys:
        v = _f(row.get(k))
        if v is not None:
            return v
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a reproducible shortlist from results_matrix.csv.")
    ap.add_argument("--in", dest="inp", default="results_matrix.csv", help="Input results matrix CSV")
    ap.add_argument("--top-k", type=int, default=5, help="How many entries to keep")
    ap.add_argument("--fpr-max", type=float, default=None, help="Keep rows with FPR_strict <= value")
    ap.add_argument(
        "--max-latency-p95",
        type=float,
        default=None,
        help="Keep rows with latency_ms_p95 <= value",
    )
    ap.add_argument("--out", default="shortlist.txt", help="Output shortlist file")
    args = ap.parse_args()

    rows = _read_csv(Path(args.inp))
    candidates = []
    for row in rows:
        u = _pick(row, "u_mean", "u")
        asr = _pick(row, "ASR_strict", "asr_strict", "asr")
        fpr = _pick(row, "FPR_strict", "fpr_strict", "fpr")
        lat95 = _pick(row, "latency_ms_p95")
        if u is None:
            continue
        if args.fpr_max is not None:
            if fpr is None or fpr > args.fpr_max:
                continue
        if args.max_latency_p95 is not None:
            if lat95 is None or lat95 > args.max_latency_p95:
                continue

        candidates.append(
            {
                "run_id": row.get("run_id", ""),
                "run_dir": row.get("run_dir", ""),
                "defense_profile": row.get("defense_profile") or row.get("defense") or "",
                "model": row.get("model", ""),
                "u_mean": u,
                "asr": asr,
                "fpr": fpr,
                "latency_ms_p95": lat95,
            }
        )

    # Prefer high utility first, then robustness, then lower FPR/latency.
    candidates.sort(
        key=lambda r: (
            -float(r["u_mean"]),
            float(r["asr"]) if r["asr"] is not None else 10.0,
            float(r["fpr"]) if r["fpr"] is not None else 10.0,
            float(r["latency_ms_p95"]) if r["latency_ms_p95"] is not None else 1e18,
            str(r["run_id"]),
        )
    )

    k = max(1, int(args.top_k))
    picked = candidates[:k]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# shortlist generated from results_matrix.csv\n")
    lines.append(
        "# columns: run_id\\tdefense_profile\\tmodel\\tu_mean\\tasr_strict\\tfpr_strict\\tlatency_ms_p95\\trun_dir\n"
    )
    for row in picked:
        lines.append(
            "\t".join(
                [
                    str(row.get("run_id") or ""),
                    str(row.get("defense_profile") or ""),
                    str(row.get("model") or ""),
                    str(row.get("u_mean") if row.get("u_mean") is not None else ""),
                    str(row.get("asr") if row.get("asr") is not None else ""),
                    str(row.get("fpr") if row.get("fpr") is not None else ""),
                    str(row.get("latency_ms_p95") if row.get("latency_ms_p95") is not None else ""),
                    str(row.get("run_dir") or ""),
                ]
            )
            + "\n"
        )

    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {len(picked)} rows (from {len(candidates)} candidates) -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
