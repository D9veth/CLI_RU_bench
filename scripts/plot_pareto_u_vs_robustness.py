#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f(x: Optional[str]) -> Optional[float]:
    try:
        if x is None:
            return None
        x = x.strip()
        if x == "" or x.lower() == "none":
            return None
        return float(x)
    except Exception:
        return None


def pareto_front(points: List[Tuple[float, float, int]]) -> List[int]:
    """Maximize (x, y). Returns indices of non-dominated points."""
    pts = sorted(points, key=lambda t: (t[0], t[1]), reverse=True)
    front = []
    best_y = -1e18
    for x, y, idx in pts:
        if y > best_y + 1e-12:
            front.append(idx)
            best_y = y
    return front


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="results_matrix.csv")
    ap.add_argument("--out", dest="out", default="pareto_u_vs_robustness.png")
    ap.add_argument("--fpr-max", type=float, default=None, help="Constraint: keep only points with FPR <= tau")
    ap.add_argument("--label", default="run_id", help="Column to annotate Pareto points")
    ap.add_argument("--color-by-fpr", action="store_true", help="Color points by FPR")
    ap.add_argument("--size-by-latency", action="store_true", help="Scale point size by latency_ms_p95")
    args = ap.parse_args()

    rows = read_csv(Path(args.inp))

    xs, ys, labels = [], [], []
    colors = []
    sizes = []

    pareto_pts = []

    # collect numeric ranges for size scaling
    lat_list = []

    for r in rows:
        u = f(r.get("u_mean")) or f(r.get("u"))
        asr = f(r.get("ASR_strict")) or f(r.get("asr_strict")) or f(r.get("asr"))
        fpr = f(r.get("FPR_strict")) or f(r.get("fpr_strict")) or f(r.get("fpr"))
        lat95 = f(r.get("latency_ms_p95"))

        if u is None or asr is None:
            continue
        robustness = 1.0 - asr

        if args.fpr_max is not None:
            if fpr is None or fpr > args.fpr_max:
                continue

        xs.append(robustness)
        ys.append(u)
        label_value = r.get(args.label)
        if label_value in {None, ""} and args.label == "defense_profile":
            label_value = r.get("defense")
        labels.append(label_value or "")

        if args.color_by_fpr:
            colors.append(fpr if fpr is not None else 0.0)

        if args.size_by_latency and lat95 is not None:
            lat_list.append(lat95)
            sizes.append(lat95)

    # size scaling (avoid manual colors; size is ok)
    if args.size_by_latency and sizes:
        mn, mx = min(sizes), max(sizes)
        if mx > mn:
            sizes = [30 + 170 * ((v - mn) / (mx - mn)) for v in sizes]
        else:
            sizes = [80 for _ in sizes]
    else:
        sizes = None

    plt.figure(figsize=(8, 6))
    if args.color_by_fpr and colors:
        sc = plt.scatter(xs, ys, c=colors, s=sizes)
        plt.colorbar(sc, label="FPR")
    else:
        plt.scatter(xs, ys, s=sizes)

    plt.xlabel("Robustness (1 - ASR), higher is better")
    plt.ylabel("U (utility mean), higher is better")
    title = "Pareto: U vs (1 - ASR)"
    if args.fpr_max is not None:
        title += f"  (FPR ≤ {args.fpr_max})"
    plt.title(title)

    # Pareto front (within filtered set)
    pts = [(xs[i], ys[i], i) for i in range(len(xs))]
    front_idx = set(pareto_front(pts))
    for i in front_idx:
        if labels[i]:
            plt.annotate(labels[i], (xs[i], ys[i]), fontsize=8)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out, dpi=200)
    print(f"Wrote plot -> {out}")


if __name__ == "__main__":
    main()
