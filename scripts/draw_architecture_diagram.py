#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


def box(ax, x, y, w, h, text):
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fill=False, linewidth=1.2)
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10)


def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Draw benchmark architecture diagram")
    ap.add_argument("--out", default="architecture_benchmark.png")
    args = ap.parse_args()

    plt.figure(figsize=(10, 6))
    ax = plt.gca()
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    box(ax, 0.5, 4.4, 1.8, 0.8, "Конфигурации\nYAML / JSON")
    box(ax, 0.5, 3.1, 1.8, 0.8, "Наборы тестов\nSafety / Utility")
    box(ax, 3.0, 4.4, 1.9, 0.8, "CLI / RunConfig\nзапуск эксперимента")
    box(ax, 3.0, 3.1, 1.9, 0.8, "DefensePipeline\nD0–D3")
    box(ax, 5.5, 4.4, 1.9, 0.8, "OpenAI-compatible\nмодель")
    box(ax, 5.5, 3.1, 1.9, 0.8, "Оценивание\nSafety + Utility")
    box(ax, 8.0, 4.4, 1.5, 0.8, "cases.jsonl\nsummary.json")
    box(ax, 8.0, 3.1, 1.5, 0.8, "results_matrix.csv\nplots / reports")
    box(ax, 3.0, 1.2, 6.5, 0.9, "Постобработка: агрегирование метрик, сравнение конфигураций, Парето-анализ")

    arrow(ax, 2.3, 4.8, 3.0, 4.8)
    arrow(ax, 2.3, 3.5, 3.0, 3.5)
    arrow(ax, 4.9, 4.8, 5.5, 4.8)
    arrow(ax, 4.9, 3.5, 5.5, 3.5)
    arrow(ax, 6.45, 4.4, 6.45, 3.9)
    arrow(ax, 7.4, 4.8, 8.0, 4.8)
    arrow(ax, 7.4, 3.5, 8.0, 3.5)
    arrow(ax, 8.75, 3.1, 8.75, 2.1)
    arrow(ax, 8.75, 4.4, 8.75, 2.1)

    plt.tight_layout()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close()
    print(f"Wrote architecture diagram to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
