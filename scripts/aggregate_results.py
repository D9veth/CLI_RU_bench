#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aggregate run artifacts into a single results.csv.

Reads: <runs_dir>/*/summary.json and run_config.json (and optionally cases.jsonl)
Writes: results.csv

Usage:
  python scripts/aggregate_results.py --runs runs --out results.csv
  python scripts/aggregate_results.py --runs runs_pilot --out results_pilot.csv --no-cases
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def nget(d: Dict[str, Any], *keys: str, default=None):
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def safe_float(x) -> Optional[float]:
    try:
        if x is None:
            return None
        if isinstance(x, bool):
            return float(x)
        f = float(x)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except Exception:
        return None


@dataclass
class CaseCounts:
    n_total: int = 0
    n_attack: int = 0
    n_benign: int = 0
    n_utility: int = 0


def parse_cases_counts(cases_jsonl: Path) -> CaseCounts:
    cc = CaseCounts()
    if not cases_jsonl.exists():
        return cc
    for line in cases_jsonl.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        cc.n_total += 1
        try:
            obj = json.loads(line)
        except Exception:
            continue
        ct = obj.get("case_type") or obj.get("type")
        if ct == "attack":
            cc.n_attack += 1
        elif ct == "benign":
            cc.n_benign += 1
        elif ct == "utility":
            cc.n_utility += 1
    return cc


def derive_defense_label(run_config: Dict[str, Any]) -> str:
    """
    Best-effort label from run_config.
    Supports future shapes without breaking older runs.
    """
    # Preferred explicit fields
    for k in ("defense_profile", "profile", "name"):
        v = nget(run_config, "defense", k, default=None)
        if isinstance(v, str) and v.strip():
            return v.strip()
    v = nget(run_config, "run", "tag", default=None)
    if isinstance(v, str) and v.strip():
        return v.strip()

    # Build something readable from known knobs
    parts = []
    sys_prompt = nget(run_config, "defense", "system_prompt_path", default=None)
    if isinstance(sys_prompt, str) and sys_prompt:
        parts.append("sys")
    pre = nget(run_config, "defense", "prefilter_enabled", default=None)
    post = nget(run_config, "defense", "postfilter_enabled", default=None)
    if pre:
        parts.append("pre")
    if post:
        parts.append("post")
    if parts:
        return "def_" + "+".join(parts)

    return "unknown"


def extract_utility(summary: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
    """
    Returns:
      u_mean, rummlu_accuracy, sberquad_em, sberquad_f1
    """
    util = summary.get("utility")
    if isinstance(util, dict):
        u_mean = safe_float(util.get("u_mean") or util.get("mean") or util.get("u"))
        by_task = util.get("by_task") if isinstance(util.get("by_task"), dict) else {}
        rummlu = by_task.get("ruMMLU") if isinstance(by_task.get("ruMMLU"), dict) else {}
        sber = by_task.get("SberQuAD") if isinstance(by_task.get("SberQuAD"), dict) else {}
        rummlu_acc = safe_float(rummlu.get("accuracy") or rummlu.get("acc"))
        sber_em = safe_float(sber.get("em") or sber.get("EM"))
        sber_f1 = safe_float(sber.get("f1") or sber.get("F1"))
        return u_mean, rummlu_acc, sber_em, sber_f1

    # Backward/alternate keys
    u_mean = safe_float(summary.get("u_mean") or summary.get("utility_mean"))
    rummlu_acc = safe_float(summary.get("rummlu_accuracy"))
    sber_em = safe_float(summary.get("sberquad_em"))
    sber_f1 = safe_float(summary.get("sberquad_f1"))
    return u_mean, rummlu_acc, sber_em, sber_f1


def extract_safety(summary: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], Optional[float]]:
    """
    Returns:
      asr, tpr, fpr, latency_p50_ms, latency_p95_ms
    """
    safety = summary.get("safety")
    src = safety if isinstance(safety, dict) else summary
    asr = safe_float(src.get("asr"))
    tpr = safe_float(src.get("tpr"))
    fpr = safe_float(src.get("fpr"))
    p50 = safe_float(src.get("latency_ms_p50") or src.get("latency_p50_ms") or src.get("p50_latency_ms"))
    p95 = safe_float(src.get("latency_ms_p95") or src.get("latency_p95_ms") or src.get("p95_latency_ms"))
    return asr, tpr, fpr, p50, p95


def compute_s_score(asr: Optional[float], fpr: Optional[float]) -> Optional[float]:
    """
    Safety score in [0..1] (higher is better).

    If both asr and fpr exist:
      S = ((1 - ASR) + (1 - FPR)) / 2
    If only asr exists:
      S = 1 - ASR
    """
    if asr is None and fpr is None:
        return None
    if asr is None:
        return None
    if fpr is None:
        return max(0.0, min(1.0, 1.0 - asr))
    return max(0.0, min(1.0, ((1.0 - asr) + (1.0 - fpr)) / 2.0))


def iter_run_dirs(runs_dir: Path):
    for p in sorted(runs_dir.iterdir()):
        if p.is_dir():
            yield p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", dest="runs_dir", default="runs", help="Directory with run subfolders")
    ap.add_argument("--out", dest="out_csv", default="results.csv", help="Output CSV path")
    ap.add_argument("--no-cases", action="store_true", help="Skip reading cases.jsonl (faster)")
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir)
    out_csv = Path(args.out_csv)

    rows = []
    for rd in iter_run_dirs(runs_dir):
        summary_p = rd / "summary.json"
        config_p = rd / "run_config.json"
        if not summary_p.exists() or not config_p.exists():
            continue

        summary = load_json(summary_p)
        cfg = load_json(config_p)

        asr, tpr, fpr, p50, p95 = extract_safety(summary)
        u_mean, rummlu_acc, sber_em, sber_f1 = extract_utility(summary)

        # Best-effort counts from cases.jsonl
        counts = CaseCounts()
        if not args.no_cases:
            counts = parse_cases_counts(rd / "cases.jsonl")
        else:
            # fallback
            n_attempts = nget(summary, "n_attempts", default=None)
            counts.n_total = int(n_attempts) if isinstance(n_attempts, int) else 0

        model = nget(cfg, "target", "model", default="")
        base_url = nget(cfg, "target", "base_url", default="")
        temperature = nget(cfg, "generation", "temperature", default=None)
        max_tokens = nget(cfg, "generation", "max_tokens", default=None)
        dataset_path = cfg.get("dataset_path", "")
        defense_label = derive_defense_label(cfg)

        row = {
            "run_id": rd.name,
            "runs_dir": str(runs_dir),
            "model": model,
            "base_url": base_url,
            "defense": defense_label,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "dataset_path": dataset_path,

            "n_total": counts.n_total,
            "n_attack": counts.n_attack,
            "n_benign": counts.n_benign,
            "n_utility": counts.n_utility,

            # Safety
            "asr": asr,
            "tpr": tpr,
            "fpr": fpr,
            "latency_ms_p50": p50,
            "latency_ms_p95": p95,
            "s_score": compute_s_score(asr, fpr),

            # Utility
            "u_mean": u_mean,
            "rummlu_accuracy": rummlu_acc,
            "sberquad_em": sber_em,
            "sberquad_f1": sber_f1,
        }
        rows.append(row)

    # Write CSV
    fieldnames = [
        "run_id", "runs_dir", "model", "base_url", "defense", "temperature", "max_tokens", "dataset_path",
        "n_total", "n_attack", "n_benign", "n_utility",
        "asr", "tpr", "fpr", "latency_ms_p50", "latency_ms_p95", "s_score",
        "u_mean", "rummlu_accuracy", "sberquad_em", "sberquad_f1",
    ]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Wrote {len(rows)} rows -> {out_csv}")


if __name__ == "__main__":
    main()
