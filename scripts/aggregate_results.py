#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aggregate completed run artifacts into a normalized results matrix.

Key properties:
- uses `defense.profile` when it is present in `run_config.json`
- keeps legacy runs without `defense.profile` as `unknown`
- skips incomplete directories without breaking aggregation
- resolves `defense_config_key` honestly when it can be proven

Examples:
  python3 scripts/aggregate_results.py --runs runs_mistral_q5 --out results_matrix.csv
  python3 scripts/aggregate_results.py \
    --runs runs_matrix --runs runs_mistral_q5 \
    --out results/results_matrix_real.csv \
    --warnings-out results/aggregation_warnings_real.csv \
    --report-json results/aggregation_report_real.json
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from bench.core.config import RunConfig


KNOWN_STATUSES = (
    "ok",
    "timeout",
    "http_error",
    "parse_error",
    "filtered_prefilter",
    "filtered_postfilter",
)

FIELDNAMES = [
    # IDs / provenance
    "run_id",
    "run_dir",
    "runs_root",
    "config_source_path",
    "config_source_name",
    "defense_config_key",
    "defense_config_path",
    "defense_config_source",
    "defense_profile_source",
    "case_count_source",
    "dataset_path",
    "dataset_id",
    "dataset_version",
    "dataset_split",
    "dataset_hash",
    "config_hash",
    "scoring_rules_hash",
    "code_version",
    "started_at",
    "finished_at",
    # Model / generation / defense
    "provider",
    "model",
    "base_url",
    "endpoint_url",
    "timeout_sec",
    "retries",
    "max_concurrency",
    "repeats",
    "temperature",
    "top_p",
    "max_tokens",
    "defense_profile",
    "defense_wrap_user_messages",
    # Reliability / counts
    "n_attempts",
    "n_ok_attempts",
    "n_failed_attempts",
    "failure_rate",
    "parse_error_rate",
    "n_safety_attempts",
    "n_utility_attempts",
    "n_total_cases",
    "n_attack_cases",
    "n_benign_cases",
    "n_utility_cases",
    "status_ok",
    "status_timeout",
    "status_http_error",
    "status_parse_error",
    "status_filtered_prefilter",
    "status_filtered_postfilter",
    "status_other",
    # Safety
    "TP",
    "FP",
    "TN",
    "FN",
    "ASR_strict",
    "ASR_lenient",
    "TPR_strict",
    "TPR_lenient",
    "FPR_strict",
    "FPR_lenient",
    "partial_rate_attack",
    "partial_rate_benign",
    "latency_ms_p50",
    "latency_ms_p95",
    "robustness",
    "safety_score",
    # Utility / quality
    "u_mean",
    "rummlu_accuracy",
    "sberquad_em",
    "sberquad_f1",
    "utility_n_scored",
    "utility_n_attempts",
    "utility_n_ok_attempts",
    # Dispersion / CI (if present)
    "asr_std",
    "asr_sem",
    "fpr_std",
    "fpr_sem",
    "u_mean_std",
    "u_mean_sem",
    "asr_ci_low",
    "asr_ci_high",
    "fpr_ci_low",
    "fpr_ci_high",
    "u_mean_ci_low",
    "u_mean_ci_high",
]

WARNING_FIELDNAMES = [
    "runs_root",
    "run_id",
    "run_dir",
    "warning_code",
    "severity",
    "message",
]


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def nget(d: Dict[str, Any], *keys: str, default=None):
    cur: Any = d
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def safe_float(x) -> Optional[float]:
    try:
        if x is None:
            return None
        if isinstance(x, bool):
            return float(x)
        value = float(x)
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    except Exception:
        return None


def safe_int(x) -> Optional[int]:
    try:
        if x is None:
            return None
        return int(x)
    except Exception:
        return None


def _summary_meta(cfg: Dict[str, Any], summary: Dict[str, Any], key: str):
    if key in cfg:
        return cfg.get(key)
    run_meta = summary.get("run_meta")
    if isinstance(run_meta, dict):
        return run_meta.get(key)
    return None


def _compute_safety_score(asr: Optional[float], fpr: Optional[float]) -> Optional[float]:
    if asr is None:
        return None
    if fpr is None:
        return max(0.0, min(1.0, 1.0 - asr))
    return max(0.0, min(1.0, ((1.0 - asr) + (1.0 - fpr)) / 2.0))


def _find_task_block(by_task: Dict[str, Any], tokens: Iterable[str]) -> Dict[str, Any]:
    for key, value in by_task.items():
        if not isinstance(value, dict):
            continue
        low = str(key).lower()
        if any(tok in low for tok in tokens):
            return value
    return {}


def _status_count(status_counts: Dict[str, Any], key: str) -> int:
    return int(safe_int(status_counts.get(key)) or 0)


def _warning(
    runs_root: Path,
    run_dir: Optional[Path],
    warning_code: str,
    message: str,
    *,
    severity: str = "warning",
) -> Dict[str, str]:
    return {
        "runs_root": str(runs_root),
        "run_id": run_dir.name if run_dir is not None else "",
        "run_dir": str(run_dir) if run_dir is not None else "",
        "warning_code": warning_code,
        "severity": severity,
        "message": message,
    }


@dataclass
class CaseCounts:
    n_total: Optional[int] = None
    n_attack: Optional[int] = None
    n_benign: Optional[int] = None
    n_utility: Optional[int] = None


def parse_cases_counts(cases_jsonl: Path) -> CaseCounts:
    counts = CaseCounts(n_total=0, n_attack=0, n_benign=0, n_utility=0)
    for line in cases_jsonl.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        counts.n_total = int(counts.n_total or 0) + 1
        try:
            obj = json.loads(line)
        except Exception:
            continue
        case_type = obj.get("case_type") or obj.get("type")
        if case_type == "attack":
            counts.n_attack = int(counts.n_attack or 0) + 1
        elif case_type == "benign":
            counts.n_benign = int(counts.n_benign or 0) + 1
        elif case_type == "utility":
            counts.n_utility = int(counts.n_utility or 0) + 1
    return counts


def fallback_case_counts(cfg: Dict[str, Any], summary: Dict[str, Any]) -> CaseCounts:
    safety = summary.get("safety") if isinstance(summary.get("safety"), dict) else {}
    utility = summary.get("utility") if isinstance(summary.get("utility"), dict) else {}
    repeats = safe_int(nget(cfg, "run", "repeats", default=None)) or 1

    attack = safe_int(safety.get("n_attack_ok_attempts"))
    if attack is None:
        attack = (safe_int(nget(safety, "counts", "TP", default=None)) or 0) + (
            safe_int(nget(safety, "counts", "FN", default=None)) or 0
        )

    benign = safe_int(safety.get("n_benign_ok_attempts"))
    if benign is None:
        benign = (safe_int(nget(safety, "counts", "FP", default=None)) or 0) + (
            safe_int(nget(safety, "counts", "TN", default=None)) or 0
        )

    utility_attempts = safe_int(utility.get("n_attempts"))
    total = safe_int(summary.get("n_attempts"))
    if total is None:
        n_safety = safe_int(summary.get("n_safety_attempts")) or 0
        n_utility = safe_int(summary.get("n_utility_attempts")) or 0
        total = n_safety + n_utility

    if total is not None and repeats > 1 and total % repeats == 0:
        total = total // repeats

    return CaseCounts(
        n_total=total,
        n_attack=attack,
        n_benign=benign,
        n_utility=utility_attempts,
    )


def _iter_run_dirs(runs_root: Path):
    for candidate in sorted(runs_root.iterdir()):
        if not candidate.is_dir():
            continue
        if candidate.name.startswith("."):
            continue
        if candidate.name == "__MACOSX":
            continue
        yield candidate


def _json_signature(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _normalized_match_subset(cfg: Dict[str, Any]) -> Dict[str, Any]:
    target = cfg.get("target") if isinstance(cfg.get("target"), dict) else {}
    generation = cfg.get("generation") if isinstance(cfg.get("generation"), dict) else {}
    defense = cfg.get("defense") if isinstance(cfg.get("defense"), dict) else {}
    run = cfg.get("run") if isinstance(cfg.get("run"), dict) else {}
    return {
        "target": {
            "provider": target.get("provider"),
            "chat_path": target.get("chat_path"),
            "timeout_sec": target.get("timeout_sec"),
            "retries": target.get("retries"),
            "max_concurrency": target.get("max_concurrency"),
            "auth_header": target.get("auth_header"),
            "auth_scheme": target.get("auth_scheme"),
            "headers": target.get("headers"),
        },
        "generation": generation,
        "defense": defense,
        "run": {
            "repeats": run.get("repeats"),
        },
    }


@dataclass
class DefenseCatalogEntry:
    key: str
    path: Path
    signature: str


def _load_defense_catalog(defenses_dir: Path) -> Dict[str, List[DefenseCatalogEntry]]:
    catalog: Dict[str, List[DefenseCatalogEntry]] = {}
    if not defenses_dir.exists() or not defenses_dir.is_dir():
        return catalog

    for path in sorted(defenses_dir.glob("*.y*ml")):
        if path.name.startswith("_"):
            continue
        try:
            run_cfg = RunConfig.load(path.resolve())
        except Exception:
            continue
        normalized = _normalized_match_subset(run_cfg.model_dump(mode="json", exclude_none=False))
        signature = _json_signature(normalized)
        catalog.setdefault(signature, []).append(
            DefenseCatalogEntry(
                key=path.stem,
                path=path.resolve(),
                signature=signature,
            )
        )
    return catalog


def _resolve_config_source_path(cfg: Dict[str, Any], repo_root: Path) -> Tuple[Optional[Path], Optional[str]]:
    for key in ("config_source_path", "source_config_path"):
        raw = cfg.get(key)
        if not isinstance(raw, str) or not raw.strip():
            continue
        raw_path = Path(raw.strip())
        if raw_path.is_absolute():
            return raw_path.resolve(), key
        return (repo_root / raw_path).resolve(), key
    return None, None


def _resolve_defense_config(
    cfg: Dict[str, Any],
    repo_root: Path,
    defense_catalog: Dict[str, List[DefenseCatalogEntry]],
) -> Tuple[Optional[str], Optional[str], str]:
    explicit_path, explicit_source = _resolve_config_source_path(cfg, repo_root)
    if explicit_path is not None:
        key = explicit_path.stem
        return key, str(explicit_path), explicit_source or "config_source_path"

    normalized = _normalized_match_subset(cfg)
    signature = _json_signature(normalized)
    matches = defense_catalog.get(signature) or []
    if len(matches) == 1:
        match = matches[0]
        return match.key, str(match.path), "signature_match"
    if len(matches) > 1:
        match = sorted(matches, key=lambda item: item.key)[0]
        return match.key, str(match.path), "signature_match_ambiguous"
    return None, None, "unresolved"


def build_row(
    run_dir: Path,
    runs_root: Path,
    *,
    include_cases: bool,
    repo_root: Path,
    defense_catalog: Dict[str, List[DefenseCatalogEntry]],
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, str]]]:
    warnings: List[Dict[str, str]] = []
    summary_path = run_dir / "summary.json"
    config_path = run_dir / "run_config.json"
    cases_path = run_dir / "cases.jsonl"

    if not config_path.exists() and not summary_path.exists():
        warnings.append(
            _warning(
                runs_root,
                run_dir,
                "missing_run_config_and_summary",
                "Skipped directory because both run_config.json and summary.json are missing.",
            )
        )
        return None, warnings

    if not config_path.exists():
        warnings.append(
            _warning(
                runs_root,
                run_dir,
                "missing_run_config",
                "Skipped directory because run_config.json is missing.",
            )
        )
        return None, warnings

    if not summary_path.exists():
        warnings.append(
            _warning(
                runs_root,
                run_dir,
                "missing_summary",
                "Skipped directory because summary.json is missing (incomplete run artifact).",
            )
        )
        return None, warnings

    try:
        cfg = load_json(config_path)
    except Exception as exc:
        warnings.append(
            _warning(
                runs_root,
                run_dir,
                "invalid_run_config_json",
                f"Skipped directory because run_config.json could not be parsed: {exc}",
            )
        )
        return None, warnings

    try:
        summary = load_json(summary_path)
    except Exception as exc:
        warnings.append(
            _warning(
                runs_root,
                run_dir,
                "invalid_summary_json",
                f"Skipped directory because summary.json could not be parsed: {exc}",
            )
        )
        return None, warnings

    safety = summary.get("safety") if isinstance(summary.get("safety"), dict) else {}
    utility = summary.get("utility") if isinstance(summary.get("utility"), dict) else {}
    by_task = utility.get("by_task") if isinstance(utility.get("by_task"), dict) else {}
    rummlu = _find_task_block(by_task, ("rummlu", "mmlu"))
    sber = _find_task_block(by_task, ("sber", "squad"))

    defense_profile = nget(cfg, "defense", "profile", default=None)
    if isinstance(defense_profile, str) and defense_profile.strip():
        defense_profile = defense_profile.strip().upper()
        defense_profile_source = "explicit"
    else:
        defense_profile = "unknown"
        defense_profile_source = "missing_legacy"
        warnings.append(
            _warning(
                runs_root,
                run_dir,
                "missing_defense_profile",
                "run_config.json does not contain defense.profile; defense_profile kept as unknown.",
                severity="info",
            )
        )

    defense_config_key, defense_config_path, defense_config_source = _resolve_defense_config(
        cfg,
        repo_root,
        defense_catalog,
    )
    if defense_config_key is None:
        warnings.append(
            _warning(
                runs_root,
                run_dir,
                "unresolved_defense_config",
                "Could not prove which configs/defenses/*.yaml produced this run; defense_config_* kept empty.",
                severity="info",
            )
        )

    case_count_source = "cases_jsonl"
    if include_cases and cases_path.exists():
        case_counts = parse_cases_counts(cases_path)
    else:
        case_counts = fallback_case_counts(cfg, summary)
        case_count_source = "summary_fallback"
        if include_cases and not cases_path.exists():
            warnings.append(
                _warning(
                    runs_root,
                    run_dir,
                    "missing_cases_jsonl",
                    "cases.jsonl is absent; case counters were approximated from summary.json.",
                    severity="info",
                )
            )

    asr_strict = safe_float(safety.get("asr_strict"))
    if asr_strict is None:
        asr_strict = safe_float(safety.get("asr"))

    fpr_strict = safe_float(safety.get("fpr_strict"))
    if fpr_strict is None:
        fpr_strict = safe_float(safety.get("fpr"))

    status_counts = summary.get("status_counts") if isinstance(summary.get("status_counts"), dict) else {}
    status_other = 0
    for key, value in status_counts.items():
        if str(key) in KNOWN_STATUSES:
            continue
        status_other += int(safe_int(value) or 0)

    config_source_path, _ = _resolve_config_source_path(cfg, repo_root)
    row: Dict[str, Any] = {
        "run_id": run_dir.name,
        "run_dir": str(run_dir.resolve()),
        "runs_root": str(runs_root.resolve()),
        "config_source_path": str(config_source_path) if config_source_path is not None else "",
        "config_source_name": (
            config_source_path.name
            if config_source_path is not None
            else str(cfg.get("config_source_name") or cfg.get("source_config_name") or "")
        ),
        "defense_config_key": defense_config_key or "",
        "defense_config_path": defense_config_path or "",
        "defense_config_source": defense_config_source,
        "defense_profile_source": defense_profile_source,
        "case_count_source": case_count_source,
        "dataset_path": _summary_meta(cfg, summary, "dataset_path"),
        "dataset_id": _summary_meta(cfg, summary, "dataset_id"),
        "dataset_version": _summary_meta(cfg, summary, "dataset_version"),
        "dataset_split": _summary_meta(cfg, summary, "dataset_split"),
        "dataset_hash": _summary_meta(cfg, summary, "dataset_hash"),
        "config_hash": _summary_meta(cfg, summary, "config_hash"),
        "scoring_rules_hash": _summary_meta(cfg, summary, "scoring_rules_hash"),
        "code_version": _summary_meta(cfg, summary, "code_version"),
        "started_at": _summary_meta(cfg, summary, "started_at"),
        "finished_at": _summary_meta(cfg, summary, "finished_at"),
        "provider": nget(cfg, "target", "provider", default=None),
        "model": nget(cfg, "target", "model", default=None),
        "base_url": nget(cfg, "target", "base_url", default=None),
        "endpoint_url": nget(cfg, "target", "endpoint_url", default=None),
        "timeout_sec": safe_int(nget(cfg, "target", "timeout_sec", default=None)),
        "retries": safe_int(nget(cfg, "target", "retries", default=None)),
        "max_concurrency": safe_int(nget(cfg, "target", "max_concurrency", default=None)),
        "repeats": safe_int(nget(cfg, "run", "repeats", default=None)),
        "temperature": safe_float(nget(cfg, "generation", "temperature", default=None)),
        "top_p": safe_float(nget(cfg, "generation", "top_p", default=None)),
        "max_tokens": safe_int(nget(cfg, "generation", "max_tokens", default=None)),
        "defense_profile": defense_profile,
        "defense_wrap_user_messages": nget(cfg, "defense", "wrap_user_messages", default=None),
        "n_attempts": safe_int(summary.get("n_attempts")),
        "n_ok_attempts": safe_int(summary.get("n_ok_attempts")),
        "n_failed_attempts": safe_int(summary.get("n_failed_attempts")),
        "failure_rate": safe_float(summary.get("failure_rate")),
        "parse_error_rate": safe_float(summary.get("parse_error_rate")),
        "n_safety_attempts": safe_int(summary.get("n_safety_attempts")),
        "n_utility_attempts": safe_int(summary.get("n_utility_attempts")),
        "n_total_cases": case_counts.n_total,
        "n_attack_cases": case_counts.n_attack,
        "n_benign_cases": case_counts.n_benign,
        "n_utility_cases": case_counts.n_utility,
        "status_ok": _status_count(status_counts, "ok"),
        "status_timeout": _status_count(status_counts, "timeout"),
        "status_http_error": _status_count(status_counts, "http_error"),
        "status_parse_error": _status_count(status_counts, "parse_error"),
        "status_filtered_prefilter": _status_count(status_counts, "filtered_prefilter"),
        "status_filtered_postfilter": _status_count(status_counts, "filtered_postfilter"),
        "status_other": status_other,
        "TP": safe_int(nget(safety, "counts", "TP", default=None)),
        "FP": safe_int(nget(safety, "counts", "FP", default=None)),
        "TN": safe_int(nget(safety, "counts", "TN", default=None)),
        "FN": safe_int(nget(safety, "counts", "FN", default=None)),
        "ASR_strict": asr_strict,
        "ASR_lenient": safe_float(safety.get("asr_lenient")),
        "TPR_strict": safe_float(safety.get("tpr_strict") if "tpr_strict" in safety else safety.get("tpr")),
        "TPR_lenient": safe_float(safety.get("tpr_lenient")),
        "FPR_strict": fpr_strict,
        "FPR_lenient": safe_float(safety.get("fpr_lenient")),
        "partial_rate_attack": safe_float(safety.get("partial_rate_attack")),
        "partial_rate_benign": safe_float(safety.get("partial_rate_benign")),
        "latency_ms_p50": safe_float(safety.get("latency_ms_p50")),
        "latency_ms_p95": safe_float(safety.get("latency_ms_p95")),
        "robustness": (1.0 - asr_strict) if asr_strict is not None else None,
        "safety_score": _compute_safety_score(asr_strict, fpr_strict),
        "u_mean": safe_float(utility.get("u_mean")),
        "rummlu_accuracy": safe_float(
            rummlu.get("u_mean")
            if rummlu.get("u_mean") is not None
            else rummlu.get("accuracy") or rummlu.get("acc")
        ),
        "sberquad_em": safe_float(
            sber.get("em_mean")
            if sber.get("em_mean") is not None
            else sber.get("em") or sber.get("EM")
        ),
        "sberquad_f1": safe_float(
            sber.get("u_mean")
            if sber.get("u_mean") is not None
            else sber.get("f1") or sber.get("F1")
        ),
        "utility_n_scored": safe_int(utility.get("n_scored")),
        "utility_n_attempts": safe_int(utility.get("n_attempts")),
        "utility_n_ok_attempts": safe_int(utility.get("n_ok_attempts")),
        "asr_std": safe_float(safety.get("asr_std")),
        "asr_sem": safe_float(safety.get("asr_sem")),
        "fpr_std": safe_float(safety.get("fpr_std")),
        "fpr_sem": safe_float(safety.get("fpr_sem")),
        "u_mean_std": safe_float(utility.get("u_mean_std")),
        "u_mean_sem": safe_float(utility.get("u_mean_sem")),
        "asr_ci_low": safe_float(safety.get("asr_ci_low")),
        "asr_ci_high": safe_float(safety.get("asr_ci_high")),
        "fpr_ci_low": safe_float(safety.get("fpr_ci_low")),
        "fpr_ci_high": safe_float(safety.get("fpr_ci_high")),
        "u_mean_ci_low": safe_float(utility.get("u_mean_ci_low")),
        "u_mean_ci_high": safe_float(utility.get("u_mean_ci_high")),
    }
    return row, warnings


def aggregate_runs(
    runs_roots: Iterable[Path],
    *,
    include_cases: bool,
    repo_root: Path,
    defenses_dir: Path,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    rows: List[Dict[str, Any]] = []
    warnings: List[Dict[str, str]] = []
    defense_catalog = _load_defense_catalog(defenses_dir.resolve())

    for runs_root in runs_roots:
        for run_dir in _iter_run_dirs(runs_root):
            row, row_warnings = build_row(
                run_dir,
                runs_root,
                include_cases=include_cases,
                repo_root=repo_root,
                defense_catalog=defense_catalog,
            )
            warnings.extend(row_warnings)
            if row is not None:
                rows.append(row)

    rows.sort(
        key=lambda row: (
            str(row.get("dataset_path") or ""),
            str(row.get("model") or ""),
            str(row.get("defense_profile") or ""),
            str(row.get("defense_config_key") or ""),
            str(row.get("runs_root") or ""),
            str(row.get("run_id") or ""),
        )
    )
    return rows, warnings


def write_csv(path: Path, fieldnames: List[str], rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_report(
    runs_roots: List[Path],
    rows: List[Dict[str, Any]],
    warnings: List[Dict[str, str]],
) -> Dict[str, Any]:
    warning_counts = Counter(item["warning_code"] for item in warnings)
    profile_source_counts = Counter(str(row.get("defense_profile_source") or "unknown") for row in rows)
    defense_config_source_counts = Counter(str(row.get("defense_config_source") or "unknown") for row in rows)
    rows_by_root = Counter(str(row.get("runs_root") or "") for row in rows)
    return {
        "runs_roots": [str(path) for path in runs_roots],
        "rows_written": len(rows),
        "warnings_written": len(warnings),
        "warning_counts": dict(sorted(warning_counts.items(), key=lambda item: item[0])),
        "defense_profile_source_counts": dict(sorted(profile_source_counts.items(), key=lambda item: item[0])),
        "defense_config_source_counts": dict(
            sorted(defense_config_source_counts.items(), key=lambda item: item[0])
        ),
        "rows_by_runs_root": dict(sorted(rows_by_root.items(), key=lambda item: item[0])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate run artifacts into a stable results matrix schema.")
    parser.add_argument(
        "--runs",
        dest="runs_roots",
        action="append",
        default=[],
        help="Directory with run subfolders. Repeat the flag to aggregate multiple runs_* roots.",
    )
    parser.add_argument("--out", dest="out_csv", default="results_matrix.csv", help="Output CSV path")
    parser.add_argument(
        "--warnings-out",
        default="aggregation_warnings.csv",
        help="Optional CSV path for aggregation warnings and skipped/incomplete artifacts.",
    )
    parser.add_argument(
        "--report-json",
        default=None,
        help="Optional JSON path for aggregation summary report.",
    )
    parser.add_argument(
        "--defenses-dir",
        default="configs/defenses",
        help="Directory used to resolve defense_config_key by exact config signature.",
    )
    parser.add_argument("--no-cases", action="store_true", help="Skip reading cases.jsonl and fall back to summary.")
    parser.add_argument(
        "--skip-missing-roots",
        action="store_true",
        help="Silently ignore missing runs roots instead of returning a non-zero exit code.",
    )
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    runs_roots = [Path(item).resolve() for item in args.runs_roots] or [repo_root / "runs"]
    missing_roots = [root for root in runs_roots if not root.exists() or not root.is_dir()]
    if missing_roots and not args.skip_missing_roots:
        for root in missing_roots:
            print(f"Runs dir not found: {root}")
        return 2
    runs_roots = [root for root in runs_roots if root.exists() and root.is_dir()]

    rows, warnings = aggregate_runs(
        runs_roots,
        include_cases=(not args.no_cases),
        repo_root=repo_root,
        defenses_dir=Path(args.defenses_dir),
    )

    out_csv = Path(args.out_csv)
    write_csv(out_csv, FIELDNAMES, rows)

    warnings_out = Path(args.warnings_out)
    write_csv(warnings_out, WARNING_FIELDNAMES, warnings)

    if args.report_json:
        report_path = Path(args.report_json)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report = build_report(runs_roots, rows, warnings)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {len(rows)} rows -> {out_csv}")
    print(f"Wrote {len(warnings)} warnings -> {warnings_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
