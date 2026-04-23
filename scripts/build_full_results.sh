#!/usr/bin/env bash
set -euo pipefail

DATASET=${1:-data/merged_safety_utility_big.jsonl}
RESULTS_DIR=${RESULTS_DIR:-results}
MODELS_CONFIG=${MODELS_CONFIG:-configs/model_matrix.yaml}
DEFENSES_DIR=${DEFENSES_DIR:-configs/defenses}
SEED=${SEED:-20260423}
MODELS=${MODELS:-}
DEFENSES=${DEFENSES:-}
RUNS_ROOTS=${RUNS_ROOTS:-}
PYTHON_BIN=${PYTHON_BIN:-}

if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
  elif [[ -x ".venv/bin/python3" ]]; then
    PYTHON_BIN=".venv/bin/python3"
  elif [[ -x ".venv/bin/python3.14" ]]; then
    PYTHON_BIN=".venv/bin/python3.14"
  elif [[ -f ".venv/bin/bench" ]]; then
    candidate=$(sed -n '1s/^#!//p' .venv/bin/bench)
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      PYTHON_BIN="$candidate"
    fi
  fi
fi

PYTHON_BIN=${PYTHON_BIN:-python3}

ARGS=(
  scripts/fill_missing_matrix.py
  --dataset "$DATASET"
  --models-config "$MODELS_CONFIG"
  --defenses-dir "$DEFENSES_DIR"
  --results-dir "$RESULTS_DIR"
  --seed "$SEED"
)

if [[ -n "$MODELS" ]]; then
  ARGS+=(--models "$MODELS")
fi

if [[ -n "$DEFENSES" ]]; then
  ARGS+=(--defenses "$DEFENSES")
fi

if [[ -n "$RUNS_ROOTS" ]]; then
  OLD_IFS=$IFS
  IFS=',' read -r -a ROOT_ITEMS <<< "$RUNS_ROOTS"
  IFS=$OLD_IFS
  for root in "${ROOT_ITEMS[@]}"; do
    root=$(printf '%s' "$root" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    if [[ -n "$root" ]]; then
      ARGS+=(--runs-root "$root")
    fi
  done
fi

"$PYTHON_BIN" "${ARGS[@]}"
