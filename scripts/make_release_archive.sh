#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-$ROOT_DIR/dist_release}"
ARCHIVE_NAME="${2:-llm_bench_release.tar.gz}"

mkdir -p "$OUT_DIR"
tar \
  --exclude='.git' \
  --exclude='.idea' \
  --exclude='.DS_Store' \
  --exclude='__MACOSX' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='.mypy_cache' \
  --exclude='.ruff_cache' \
  --exclude='.venv' \
  --exclude='venv' \
  --exclude='backend/.venv' \
  --exclude='frontend/node_modules' \
  --exclude='frontend/dist' \
  --exclude='backend/db.sqlite3' \
  --exclude='.env' \
  --exclude='.env.*' \
  --exclude='*.pyc' \
  -czf "$OUT_DIR/$ARCHIVE_NAME" \
  -C "$ROOT_DIR" \
  README.md Makefile pyproject.toml bench configs prompts policies schemas data tests scripts backend frontend \
  results results_matrix.csv artifacts examples 2>/dev/null || true

echo "$OUT_DIR/$ARCHIVE_NAME"
