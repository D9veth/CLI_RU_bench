#!/usr/bin/env bash
set -euo pipefail

bench validate-dataset --in data/regression/dlp_cases.jsonl --out /tmp/llm_bench_dlp_validation.json
bench validate-dataset --in data/regression/prompt_injection_cases.jsonl --out /tmp/llm_bench_pi_validation.json
bench validate-dataset --in data/regression/schema_cases.jsonl --out /tmp/llm_bench_schema_validation.json
bench validate-dataset --in data/regression/benign_false_positive_cases.jsonl --out /tmp/llm_bench_benign_validation.json
bench validate-dataset --in data/regression/smoke_50.jsonl --out /tmp/llm_bench_smoke_validation.json
