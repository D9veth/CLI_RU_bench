#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Optional

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

MODEL_ORDER = ["Gemma 3 12B", "Qwen 2.5 7B", "Llama 3.1 8B", "Mistral 7B Q5"]
PROFILE_ORDER = ["D0", "D1", "D2", "D3"]
REPRESENTATIVE_KEYS = ["d0_base", "d1_base", "d2_base", "d3_strict"]


def _mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _draw_profile_chart(df: pd.DataFrame, value_col: str, ylabel: str, title: str, out_path: Path) -> None:
    plt.figure(figsize=(8, 5))
    x = np.arange(len(PROFILE_ORDER))
    for model in MODEL_ORDER:
        sub = df[df["model_name"] == model].copy()
        if sub.empty:
            continue
        sub = sub.set_index("defense_profile").reindex(PROFILE_ORDER)
        plt.plot(x, sub[value_col].values, marker="o", label=model)
    plt.xticks(x, PROFILE_ORDER)
    plt.xlabel("Профиль защиты")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()


def _draw_pareto(df: pd.DataFrame, out_path: Path) -> None:
    plt.figure(figsize=(8, 6))
    for model in MODEL_ORDER:
        sub = df[df["model_name"] == model]
        if sub.empty:
            continue
        plt.scatter(sub["one_minus_asr"], sub["u_mean"], label=model)
        for _, row in sub.iterrows():
            label = row["defense_config_key"]
            plt.annotate(label, (row["one_minus_asr"], row["u_mean"]), fontsize=7)
    plt.xlabel("1 - ASR")
    plt.ylabel("U_mean")
    plt.title("Компромисс между полезностью и устойчивостью")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()


def _draw_heatmap(cat_df: pd.DataFrame, out_path: Path) -> None:
    wanted = [
        "prompt_injection_jailbreak",
        "policy_override",
        "system_prompt_leak",
        "data_exfiltration",
        "leakage_exfiltration",
        "format_breaking_insecure_output",
        "multi_turn_escalation",
    ]
    pivot = (
        cat_df[cat_df["category"].isin(wanted)]
        .pivot(index="category", columns="defense_profile", values="asr")
        .reindex(index=wanted, columns=PROFILE_ORDER)
    )
    plt.figure(figsize=(8, 5.8))
    im = plt.imshow(pivot.values, aspect="auto")
    plt.colorbar(im, label="ASR")
    plt.xticks(range(len(PROFILE_ORDER)), PROFILE_ORDER)
    plt.yticks(range(len(wanted)), [
        "prompt injection / jailbreak",
        "policy override",
        "system prompt leak",
        "data exfiltration",
        "leakage / exfiltration",
        "format breaking",
        "multi-turn escalation",
    ])
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            if pd.notna(val):
                plt.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=8)
    plt.title("Средняя ASR по классам атак")
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()


def _draw_reliability(df: pd.DataFrame, out_path: Path) -> None:
    metric = (
        df.groupby(["model_name", "defense_profile"], as_index=False)[["failure_rate", "parse_error_rate"]]
        .mean()
        .sort_values(["model_name", "defense_profile"])
    )
    # choose failure_rate for plot
    plt.figure(figsize=(8, 5))
    x = np.arange(len(PROFILE_ORDER))
    for model in MODEL_ORDER:
        sub = metric[metric["model_name"] == model].set_index("defense_profile").reindex(PROFILE_ORDER)
        if sub.empty:
            continue
        plt.plot(x, sub["failure_rate"].values, marker="o", label=model)
    plt.xticks(x, PROFILE_ORDER)
    plt.xlabel("Профиль защиты")
    plt.ylabel("Failure rate")
    plt.title("Надёжность прогона по профилям защиты")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()


def _draw_variant_bars(df: pd.DataFrame, profile: str, metric: str, ylabel: str, title: str, out_path: Path) -> None:
    sub = df[df["defense_profile"] == profile].copy()
    order = sub.groupby("defense_config_key")[metric].mean().sort_values(ascending=(metric not in {"u_mean", "one_minus_asr"})).index.tolist()
    grp = sub.groupby("defense_config_key", as_index=False)[metric].mean()
    grp["rank_key"] = grp["defense_config_key"].map({k: i for i, k in enumerate(order)})
    grp = grp.sort_values("rank_key")
    plt.figure(figsize=(8, 5))
    plt.bar(grp["defense_config_key"], grp[metric])
    plt.xticks(rotation=30, ha="right")
    plt.ylabel(ylabel)
    plt.xlabel("Вариант конфигурации")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate chapter-ready plots from results_matrix.csv and analysis exports")
    ap.add_argument("--results", default="results_matrix.csv")
    ap.add_argument("--exports-dir", default="analysis_exports")
    ap.add_argument("--out-dir", default="figures")
    args = ap.parse_args()

    results_path = Path(args.results)
    exports_dir = Path(args.exports_dir)
    out_dir = Path(args.out_dir)
    _mkdir(out_dir)

    df = pd.read_csv(results_path)
    if "model_name" not in df.columns:
        mapping = {
            "Qwen/Qwen2.5-7B-Instruct": "Qwen 2.5 7B",
            "meta-llama/Llama-3.1-8B-Instruct": "Llama 3.1 8B",
            "google/gemma-3-12b": "Gemma 3 12B",
            "mistral-7b-instruct-v0.3@q5_k_m": "Mistral 7B Q5",
        }
        df["model_name"] = df["model"].map(lambda x: mapping.get(str(x), str(x)))
    df["one_minus_asr"] = 1.0 - df["ASR_strict"]

    rep = df[df["defense_config_key"].isin(REPRESENTATIVE_KEYS)].copy()
    rep = rep.sort_values(["model_name", "defense_profile"])

    _draw_profile_chart(rep, "ASR_strict", "ASR", "Успешность атак по основным профилям", out_dir / "fig_01_asr_profiles.png")
    _draw_profile_chart(rep, "FPR_strict", "FPR", "Ложные блокировки по основным профилям", out_dir / "fig_02_fpr_profiles.png")
    _draw_profile_chart(rep, "u_mean", "U_mean", "Полезность по основным профилям", out_dir / "fig_03_utility_profiles.png")
    _draw_profile_chart(rep, "latency_ms_p95", "Latency p95, ms", "Задержка p95 по основным профилям", out_dir / "fig_04_latency_profiles.png")
    _draw_pareto(df, out_dir / "fig_05_pareto_all_points.png")

    cat_summary_path = exports_dir / "category_attack_summary.csv"
    if cat_summary_path.exists():
        cat_summary = pd.read_csv(cat_summary_path)
        _draw_heatmap(cat_summary, out_dir / "fig_06_attack_heatmap.png")

    _draw_reliability(df, out_dir / "fig_07_reliability_profiles.png")
    _draw_variant_bars(df, "D2", "ASR_strict", "ASR", "Сравнение вариантов D2", out_dir / "fig_08_d2_variants_asr.png")
    _draw_variant_bars(df, "D3", "ASR_strict", "ASR", "Сравнение вариантов D3", out_dir / "fig_09_d3_variants_asr.png")
    _draw_variant_bars(df, "D3", "u_mean", "U_mean", "Полезность вариантов D3", out_dir / "fig_10_d3_variants_utility.png")

    print(f"Wrote figure suite to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
