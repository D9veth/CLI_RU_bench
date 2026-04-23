#!/usr/bin/env bash
set -euo pipefail

RESULTS=${1:-results_matrix.csv}
RUNS_ROOT=${2:-runs_matrix}
OUT_ROOT=${3:-chapter_assets}

mkdir -p "$OUT_ROOT"
python3 scripts/build_analysis_exports.py --results "$RESULTS" --runs-root "$RUNS_ROOT" --out-dir "$OUT_ROOT/analysis_exports"
python3 scripts/plot_results_suite.py --results "$RESULTS" --exports-dir "$OUT_ROOT/analysis_exports" --out-dir "$OUT_ROOT/figures"
python3 scripts/draw_architecture_diagram.py --out "$OUT_ROOT/figures/fig_00_architecture.png"

echo "All chapter assets are in: $OUT_ROOT"
