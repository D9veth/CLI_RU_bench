#!/usr/bin/env bash
set -euo pipefail

DATASET=${1:-data/merged_safety_utility.jsonl}
BASE_URL=${BASE_URL:-http://localhost:8000/v1}
MODEL=${MODEL:-your-model}
OUT=${OUT:-runs_ablation}
API_KEY_ENV=${API_KEY_ENV:-OPENAI_API_KEY}
SPLIT=${SPLIT:-dev}
DATASET_VERSION=${DATASET_VERSION:-}
REPEATS=${REPEATS:-1}
SKIP_PREFLIGHT=${SKIP_PREFLIGHT:-0}

if [[ ! -f "$DATASET" ]]; then
  echo "Dataset file not found: $DATASET" >&2
  exit 2
fi

mkdir -p "$OUT"

echo "Dataset: $DATASET"
echo "Split: $SPLIT"
echo "Model: $MODEL"
echo "Out: $OUT"
echo

echo "Running ablation matrix configs/defenses_ablation/*.yaml"
for cfg in configs/defenses_ablation/*.yaml; do
  name=$(basename "$cfg" .yaml)
  echo "--- $name ---"
  cmd=(
    bench run
    -c "$cfg"
    -d "$DATASET"
    --split "$SPLIT"
    --base-url "$BASE_URL"
    --model "$MODEL"
    --api-key-env "$API_KEY_ENV"
    --repeats "$REPEATS"
    -o "$OUT"
  )
  if [[ -n "$DATASET_VERSION" ]]; then
    cmd+=(--dataset-version "$DATASET_VERSION")
  fi
  if [[ "$SKIP_PREFLIGHT" == "1" ]]; then
    cmd+=(--skip-preflight)
  fi
  "${cmd[@]}"
  echo
done

echo "Done. Ablation runs are in: $OUT"
