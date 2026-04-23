#!/usr/bin/env bash
set -euo pipefail

DATASET=${1:-data/merged_safety_utility.jsonl}
BASE_URL=${BASE_URL:-http://localhost:8000/v1}
MODEL=${MODEL:-your-model}
OUT=${OUT:-runs}
API_KEY_ENV=${API_KEY_ENV:-OPENAI_API_KEY}

if command -v bench >/dev/null 2>&1; then
  BENCH_CMD=(bench)
else
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
  BENCH_CMD=("$PYTHON_BIN" -m bench.cli)
fi

if [[ ! -f "$DATASET" ]]; then
  echo "Dataset file not found: $DATASET" >&2
  exit 2
fi

mkdir -p "$OUT"

echo "Dataset: $DATASET"
echo "Base URL: $BASE_URL"
echo "Model: $MODEL"
echo "Out: $OUT"
echo

echo "Running defense matrix configs/defenses/*.yaml"

for cfg in configs/defenses/*.yaml; do
  if [[ "$cfg" == *"_target_placeholder.yaml" ]]; then
    continue
  fi
  if [[ "$cfg" == *"smoke"* ]]; then
    continue
  fi
  name=$(basename "$cfg" .yaml)
  echo "--- $name ---"
  "${BENCH_CMD[@]}" run \
    -c "$cfg" \
    -d "$DATASET" \
    --base-url "$BASE_URL" \
    --model "$MODEL" \
    --api-key-env "$API_KEY_ENV" \
    -o "$OUT"
  echo
done

echo "Done. Results are in: $OUT"
