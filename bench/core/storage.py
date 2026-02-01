from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
import secrets

from bench.core.config import RunConfig
from bench.core.preflight import PreflightResult

def create_run_dir(out_root: Path) -> tuple[Path, str]:
    out_root.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{ts}_{secrets.token_hex(3)}"
    run_dir = out_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir, run_id

def write_run_config(run_dir: Path, run_cfg: RunConfig, dataset_path: str):
    payload = run_cfg.model_dump()
    payload["dataset_path"] = dataset_path
    (run_dir / "run_config.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def write_preflight(run_dir: Path, preflight: PreflightResult):
    (run_dir / "preflight.json").write_text(
        json.dumps(preflight.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def write_cases_jsonl(run_dir: Path, rows: list[dict]):
    p = run_dir / "cases.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def write_summary(run_dir: Path, summary: dict):
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

def write_report(run_dir: Path, summary: dict):
    lines = []
    lines.append("# Benchmark report\n")
    lines.append(f"- Attempts: {summary.get('n_attempts')}\n")
    lines.append(f"- ASR: {summary.get('asr')}\n")
    lines.append(f"- TPR: {summary.get('tpr')}\n")
    lines.append(f"- FPR: {summary.get('fpr')}\n")
    lines.append(f"- Latency p50 (ms): {summary.get('latency_ms_p50')}\n")
    lines.append(f"- Latency p95 (ms): {summary.get('latency_ms_p95')}\n\n")
    lines.append("## By category\n")
    for cat, v in (summary.get("by_category") or {}).items():
        lines.append(f"### {cat}\n")
        lines.append(f"- ASR: {v.get('asr')}\n")
        lines.append(f"- TPR: {v.get('tpr')}\n")
        lines.append(f"- FPR: {v.get('fpr')}\n")
        lines.append(f"- Latency p95 (ms): {v.get('latency_ms_p95')}\n\n")

    (run_dir / "report.md").write_text("".join(lines), encoding="utf-8")
