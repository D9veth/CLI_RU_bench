#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plot U vs safety score (Pareto) from results_matrix.csv.

Usage:
  python scripts/plot_pareto.py --in results_matrix.csv --out pareto.png
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f(x: str) -> Optional[float]:
    try:
        if x is None:
            return None
        x = x.strip()
        if x == "" or x.lower() == "none":
            return None
        return float(x)
    except Exception:
        return None


def pick_float(row: Dict[str, str], *keys: str) -> Optional[float]:
    for key in keys:
        value = f(row.get(key))
        if value is not None:
            return value
    return None


def pareto_front(points: List[Tuple[float, float, int]]) -> List[int]:
    """
    Maximize (S, U). Returns indices of non-dominated points.
    points: list of (S, U, idx)
    """
    pts = sorted(points, key=lambda t: (t[0], t[1]), reverse=True)
    front = []
    best_u = -1e9
    for s, u, idx in pts:
        if u > best_u:
            front.append(idx)
            best_u = u
    return front


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="results_matrix.csv")
    ap.add_argument("--out", dest="out", default="pareto.png")
    ap.add_argument("--label", dest="label", default="defense_profile", help="Which column to use as point label")
    args = ap.parse_args()

    rows = read_csv(Path(args.inp))
    xs, ys, labels = [], [], []
    pareto_pts = []
    for i, r in enumerate(rows):
        s = pick_float(r, "safety_score", "s_score")
        u = pick_float(r, "u_mean", "u")
        if s is None or u is None:
            continue
        xs.append(s)
        ys.append(u)
        label_value = r.get(args.label)
        if label_value in {None, ""} and args.label == "defense_profile":
            label_value = r.get("defense")
        labels.append(label_value or r.get("run_id", str(i)))
        pareto_pts.append((s, u, len(xs)-1))

    # Scatter
    plt.figure(figsize=(7, 5))
    plt.scatter(xs, ys)
    plt.xlabel("S (safety score, higher is better)")
    plt.ylabel("U (utility mean, higher is better)")
    plt.title("U vs S (Pareto view)")

    # Pareto front
    front_idx = set(pareto_front(pareto_pts))
    for j in range(len(xs)):
        if j in front_idx:
            plt.annotate(labels[j], (xs[j], ys[j]), fontsize=8)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out, dpi=200)
    print(f"Wrote plot -> {out}")


if __name__ == "__main__":
    main()
