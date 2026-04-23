#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd


MODEL_LABELS = {
    "Qwen/Qwen2.5-7B-Instruct": "Qwen 2.5 7B",
    "meta-llama/Llama-3.1-8B-Instruct": "Llama 3.1 8B",
    "google/gemma-3-12b": "Gemma 3 12B",
    "mistral-7b-instruct-v0.3@q5_k_m": "Mistral 7B Q5",
}

REPRESENTATIVE_KEYS = ["d0_base", "d1_base", "d2_base", "d3_strict"]


def _model_name(raw: str) -> str:
    return MODEL_LABELS.get(str(raw), str(raw))


def _case_iter(paths: Iterable[Path]):
    for path in paths:
        run_id = path.parent.name
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                obj["run_id"] = run_id
                yield obj


def _safe_ratio(a: int, b: int) -> Optional[float]:
    return (a / b) if b else None


def build_category_metrics(results_df: pd.DataFrame, cases_root: Path) -> pd.DataFrame:
    run_meta = results_df.set_index("run_id")[["model_name", "defense_config_key", "defense_profile"]].to_dict("index")
    records: List[Dict[str, object]] = []

    case_paths = sorted(cases_root.glob("*/cases.jsonl"))
    grouped: Dict[tuple[str, str], Counter] = defaultdict(Counter)
    for row in _case_iter(case_paths):
        run_id = row["run_id"]
        if run_id not in run_meta:
            continue
        key = (run_id, str(row.get("category") or "unknown"))
        c = grouped[key]
        c["n_rows"] += 1
        if row.get("status") != "ok":
            c["n_non_ok"] += 1
            continue
        c["n_ok"] += 1
        case_type = str(row.get("case_type") or "")
        if case_type == "attack":
            c["n_attack"] += 1
            if row.get("success_attack") is True:
                c["n_attack_success"] += 1
            if row.get("blocked_attack") is True:
                c["n_attack_blocked"] += 1
        elif case_type == "benign":
            c["n_benign"] += 1
            if row.get("false_positive") is True:
                c["n_false_positive"] += 1
            if row.get("true_negative") is True:
                c["n_true_negative"] += 1
        elif case_type == "utility":
            c["n_utility"] += 1
            score = row.get("utility_score")
            try:
                if score is not None:
                    c["utility_sum"] += float(score)
                    c["utility_n_scored"] += 1
            except Exception:
                pass

    for (run_id, category), c in sorted(grouped.items()):
        meta = run_meta[run_id]
        rec: Dict[str, object] = {
            "run_id": run_id,
            "model_name": meta["model_name"],
            "defense_config_key": meta["defense_config_key"],
            "defense_profile": meta["defense_profile"],
            "category": category,
            "n_rows": c.get("n_rows", 0),
            "n_ok": c.get("n_ok", 0),
            "n_non_ok": c.get("n_non_ok", 0),
            "n_attack": c.get("n_attack", 0),
            "n_benign": c.get("n_benign", 0),
            "n_utility": c.get("n_utility", 0),
            "n_attack_success": c.get("n_attack_success", 0),
            "n_attack_blocked": c.get("n_attack_blocked", 0),
            "n_false_positive": c.get("n_false_positive", 0),
            "n_true_negative": c.get("n_true_negative", 0),
            "utility_n_scored": c.get("utility_n_scored", 0),
        }
        rec["asr"] = _safe_ratio(c.get("n_attack_success", 0), c.get("n_attack", 0))
        rec["tpr"] = _safe_ratio(c.get("n_attack_blocked", 0), c.get("n_attack", 0))
        rec["fpr"] = _safe_ratio(c.get("n_false_positive", 0), c.get("n_benign", 0))
        rec["utility_mean"] = _safe_ratio(c.get("utility_sum", 0), c.get("utility_n_scored", 0))
        records.append(rec)

    return pd.DataFrame(records)


def build_implementation_notes(results_df: pd.DataFrame, out_path: Path) -> None:
    parse_mean = float(results_df["parse_error_rate"].mean())
    fail_mean = float(results_df["failure_rate"].mean())
    pre_hits = int(results_df.get("status_filtered_prefilter", pd.Series(dtype=int)).fillna(0).sum())
    post_hits = int(results_df.get("status_filtered_postfilter", pd.Series(dtype=int)).fillna(0).sum())

    lines = []
    lines.append("# Technical implementation audit\n")
    lines.append("\n")
    lines.append("## What is already implemented\n")
    lines.append("- CLI runner with YAML/JSON configuration, artifact storage, progress files and per-run summaries.\n")
    lines.append("- Unified results matrix with safety, utility, latency and reliability metrics.\n")
    lines.append("- Multi-profile defense pipeline (D0-D3) with system prompt, message wrapping and regex-based pre/post filters.\n")
    lines.append("- Utility scoring for ruMMLU and SberQuAD plus Pareto-style post-processing scripts.\n")
    lines.append("\n")
    lines.append("## What is still missing or incomplete\n")
    lines.append("1. `json_schema_path` is declared in the configuration model, but there is no execution-time JSON Schema validation in the defense pipeline.\n")
    lines.append("2. There is no separate moderation or DLP classifier module in the current code path; D3 is currently implemented as a stricter combination of prompts, wrapping and regex filters.\n")
    lines.append("3. No interactive dashboard is present in the repository; reporting is currently limited to CSV/JSONL/Markdown artifacts and offline plotting scripts.\n")
    lines.append("4. Token usage and monetary cost are not written into the run artifacts, therefore the cost metric from the specification is not yet available.\n")
    lines.append("5. Repeated launches are formally supported, but the current matrix is almost entirely based on single repeats, so confidence intervals remain mostly unavailable.\n")
    lines.append("6. The benchmark contains multi-turn escalation cases, but there is no executable RAG/tool-use environment in the runtime loop; these scenarios are still approximated by static message histories.\n")
    lines.append("7. The automatic grader is heuristic: refusal patterns plus goal indicators. A dedicated calibration layer against manual labels is not yet implemented in the repository.\n")
    lines.append("\n")
    lines.append("## Signals from the collected results\n")
    lines.append(f"- Mean parse-error rate across the matrix: **{parse_mean:.2%}**.\n")
    lines.append(f"- Mean failure rate across the matrix: **{fail_mean:.2%}**.\n")
    lines.append(f"- Prefilter hard blocks recorded in the aggregated matrix: **{pre_hits}**.\n")
    lines.append(f"- Postfilter hard blocks recorded in the aggregated matrix: **{post_hits}**.\n")
    lines.append("- Zero hard filter hits in the current matrix indicate that the present regex rules are either too narrow for the dataset or that most gains come from prompt conditioning and generation constraints rather than from explicit filter actions.\n")
    out_path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build chapter-ready analysis tables from results_matrix.csv and runs_matrix/*/cases.jsonl")
    ap.add_argument("--results", default="results_matrix.csv")
    ap.add_argument("--runs-root", default="runs_matrix")
    ap.add_argument("--out-dir", default="analysis_exports")
    args = ap.parse_args()

    results_path = Path(args.results)
    runs_root = Path(args.runs_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(results_path)
    df["model_name"] = df["model"].map(_model_name)
    df["one_minus_asr"] = 1.0 - df["ASR_strict"]
    df["latency_sec_p95"] = df["latency_ms_p95"] / 1000.0

    representative = (
        df[df["defense_config_key"].isin(REPRESENTATIVE_KEYS)]
        .sort_values(["model_name", "defense_config_key"])
        .copy()
    )
    representative.to_csv(out_dir / "representative_matrix.csv", index=False)

    profile_summary = (
        df.groupby(["model_name", "defense_profile"], as_index=False)[
            ["ASR_strict", "FPR_strict", "u_mean", "latency_ms_p95", "failure_rate", "parse_error_rate"]
        ]
        .mean()
        .sort_values(["model_name", "defense_profile"])
    )
    profile_summary.to_csv(out_dir / "profile_summary.csv", index=False)

    variant_summary = (
        df.groupby(["defense_config_key"], as_index=False)[
            ["ASR_strict", "FPR_strict", "u_mean", "latency_ms_p95", "failure_rate", "parse_error_rate"]
        ]
        .mean()
        .sort_values(["ASR_strict", "FPR_strict", "u_mean"], ascending=[True, True, False])
    )
    variant_summary.to_csv(out_dir / "variant_summary.csv", index=False)

    shortlist_005 = (
        df[df["FPR_strict"] <= 0.05]
        .sort_values(["one_minus_asr", "u_mean", "latency_ms_p95"], ascending=[False, False, True])
        .copy()
    )
    shortlist_005.to_csv(out_dir / "shortlist_fpr_le_0_05.csv", index=False)

    shortlist_010 = (
        df[df["FPR_strict"] <= 0.10]
        .sort_values(["one_minus_asr", "u_mean", "latency_ms_p95"], ascending=[False, False, True])
        .copy()
    )
    shortlist_010.to_csv(out_dir / "shortlist_fpr_le_0_10.csv", index=False)

    category_df = build_category_metrics(df, runs_root)
    category_df.to_csv(out_dir / "category_metrics.csv", index=False)

    category_attack_summary = (
        category_df[category_df["n_attack"] > 0]
        .groupby(["defense_profile", "category"], as_index=False)["asr"]
        .mean()
        .sort_values(["category", "defense_profile"])
    )
    category_attack_summary.to_csv(out_dir / "category_attack_summary.csv", index=False)

    build_implementation_notes(df, out_dir / "technical_audit.md")

    print(f"Wrote analysis exports to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
