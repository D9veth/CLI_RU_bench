from __future__ import annotations

import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import secrets
import subprocess
from typing import Any, Dict, Iterator, Optional

from bench.core.config import RunConfig
from bench.core.preflight import PreflightResult


_SCORING_RULES_PATH = Path(__file__).resolve().parents[1] / "scoring_rules.yaml"


def utc_now_iso() -> str:
    # UTC timestamp in a stable artifact-friendly format.
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def create_run_dir(out_root: Path) -> tuple[Path, str]:
    out_root.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{ts}_{secrets.token_hex(3)}"
    run_dir = out_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir, run_id


def _normalized_config_payload(run_cfg: RunConfig) -> Dict[str, Any]:
    return run_cfg.model_dump(mode="json", exclude_none=False)


def _config_hash_sha256(run_cfg: RunConfig) -> str:
    normalized = _normalized_config_payload(run_cfg)
    serialized = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def config_hash_sha256(run_cfg: RunConfig) -> str:
    return _config_hash_sha256(run_cfg)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _git_code_version(cwd: Optional[Path] = None) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(cwd or Path.cwd()),
            capture_output=True,
            text=True,
            check=True,
        )
        sha = proc.stdout.strip()
        return sha or "unknown"
    except Exception:
        return "unknown"


def _scoring_rules_hash(path: Optional[Path] = None) -> str:
    candidate = (path or _SCORING_RULES_PATH).resolve()
    if not candidate.exists():
        return "unknown"
    try:
        return sha256_file(candidate)
    except Exception:
        return "unknown"


def build_run_metadata(
    run_cfg: RunConfig,
    *,
    dataset_path: str,
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_split: Optional[str] = None,
    dataset_hash: Optional[str] = None,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
) -> Dict[str, Any]:
    meta = {
        "dataset_path": dataset_path,
        "dataset_id": dataset_id or dataset_path,
        "dataset_version": dataset_version,
        "dataset_split": dataset_split,
        "dataset_hash": dataset_hash,
        "config_hash": _config_hash_sha256(run_cfg),
        "scoring_rules_hash": _scoring_rules_hash(),
        "code_version": _git_code_version(cwd=run_cfg.source_dir),
        "started_at": started_at,
        "finished_at": finished_at,
    }
    if run_cfg.source_path is not None:
        meta["config_source_path"] = str(run_cfg.source_path)
        meta["config_source_name"] = run_cfg.source_path.name
    return meta


def write_run_config(
    run_dir: Path,
    run_cfg: RunConfig,
    dataset_path: str,
    *,
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_split: Optional[str] = None,
    dataset_hash: Optional[str] = None,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
) -> Dict[str, Any]:
    payload = _normalized_config_payload(run_cfg)
    run_meta = build_run_metadata(
        run_cfg,
        dataset_path=dataset_path,
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_split=dataset_split,
        dataset_hash=dataset_hash,
        started_at=started_at,
        finished_at=finished_at,
    )
    payload.update(run_meta)
    (run_dir / "run_config.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return run_meta

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


def iter_cases_jsonl(path: Path) -> Iterator[dict]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield obj


def read_completed_attempts(run_dir: Path) -> set[tuple[str, int]]:
    completed: set[tuple[str, int]] = set()
    cases_path = run_dir / "cases.jsonl"
    for row in iter_cases_jsonl(cases_path):
        case_id = row.get("case_id")
        repeat = row.get("repeat")
        if not isinstance(case_id, str):
            continue
        try:
            rep_i = int(repeat)
        except Exception:
            continue
        completed.add((case_id, rep_i))
    return completed


def append_case_row(run_dir: Path, row: dict) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    p = run_dir / "cases.jsonl"
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()


def write_progress(
    run_dir: Path,
    done: int,
    total: int,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    payload: Dict[str, Any] = {
        "done": int(done),
        "total": int(total),
        "updated_at": utc_now_iso(),
    }
    if isinstance(extra, dict):
        payload.update(extra)
    (run_dir / "progress.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def write_summary(run_dir: Path, summary: dict, run_meta: Optional[Dict[str, Any]] = None):
    if run_meta:
        summary = dict(summary)
        summary["run_meta"] = run_meta
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

def write_report(run_dir: Path, summary: dict):
    lines = []
    lines.append("# Benchmark report\n")
    lines.append(f"- Attempts (all): {summary.get('n_attempts')}\n")
    lines.append(f"- Attempts (safety): {summary.get('n_safety_attempts')}\n")
    lines.append(f"- Attempts (utility): {summary.get('n_utility_attempts')}\n\n")

    safety = (summary.get("safety") or {})
    util = (summary.get("utility") or {})

    lines.append("## Safety metrics\n")
    lines.append(f"- ASR: {safety.get('asr')}\n")
    lines.append(f"- TPR: {safety.get('tpr')}\n")
    lines.append(f"- FPR: {safety.get('fpr')}\n")
    lines.append(f"- Latency p50 (ms): {safety.get('latency_ms_p50')}\n")
    lines.append(f"- Latency p95 (ms): {safety.get('latency_ms_p95')}\n\n")

    lines.append("### By category\n")
    for cat, v in (safety.get("by_category") or {}).items():
        lines.append(f"#### {cat}\n")
        lines.append(f"- ASR: {v.get('asr')}\n")
        lines.append(f"- TPR: {v.get('tpr')}\n")
        lines.append(f"- FPR: {v.get('fpr')}\n")
        lines.append(f"- Latency p95 (ms): {v.get('latency_ms_p95')}\n\n")

    lines.append("## Utility metrics\n")
    lines.append(f"- U mean (average utility_score): {util.get('u_mean')}\n")
    lines.append(f"- Utility attempts scored: {util.get('n_scored')} / {util.get('n_attempts')}\n\n")
    lines.append("### By task\n")
    for t, v in (util.get("by_task") or {}).items():
        lines.append(f"#### {t}\n")
        lines.append(f"- U mean: {v.get('u_mean')}\n")
        if v.get("em_mean") is not None:
            lines.append(f"- EM mean: {v.get('em_mean')}\n")
        lines.append(f"- N: {v.get('n')}\n\n")

    (run_dir / "report.md").write_text("".join(lines), encoding="utf-8")
