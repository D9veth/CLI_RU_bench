#!/usr/bin/env bash
set -euo pipefail

DATASET=${1:-data/merged_safety_utility.jsonl}
BASE_URL=${BASE_URL:-http://localhost:8000/v1}
MODEL=${MODEL:-your-model}
OUT=${OUT:-runs}
API_KEY_ENV=${API_KEY_ENV:-OPENAI_API_KEY}

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
  name=$(basename "$cfg" .yaml)
  echo "--- $name ---"
  bench run \
    -c "$cfg" \
    -d "$DATASET" \
    --base-url "$BASE_URL" \
    --model "$MODEL" \
    --api-key-env "$API_KEY_ENV" \
    -o "$OUT"
  echo
done

echo "Done. Results are in: $OUT"
