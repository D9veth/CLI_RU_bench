from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


CASE_FILE_NAMES = {"cases.jsonl", "case_results.jsonl", "responses.jsonl"}

BLIND_COLUMNS = [
    "sample_id",
    "run_id",
    "case_id",
    "model",
    "defense_profile",
    "dataset",
    "split",
    "category",
    "status",
    "prompt",
    "model_output",
    "expected_behavior",
    "human_attack_success",
    "human_refusal",
    "human_leakage",
    "human_policy_violation",
    "human_false_refusal",
    "human_ambiguous",
    "human_comment",
]

EVALUATOR_FIELDS = [
    "evaluator_attack_success",
    "evaluator_refusal",
    "evaluator_safe_refusal",
    "evaluator_false_refusal",
    "evaluator_leakage",
    "evaluator_policy_violation",
    "evaluator_blocked",
    "evaluator_parse_error",
    "evaluator_dlp_hit",
    "evaluator_policy_block",
    "evaluator_schema_violation",
]

NORMALIZED_FIELDS = [
    "sample_id",
    "source_file",
    "source_row_index",
    "run_id",
    "case_id",
    "model",
    "defense_profile",
    "dataset",
    "split",
    "category",
    "status",
    "is_attack",
    "is_benign",
    "is_utility",
    "is_borderline",
    "prompt",
    "model_output",
    "expected_behavior",
    *EVALUATOR_FIELDS,
]

BOOL_TRUE = {"1", "true", "yes", "y", "да", "истина", "t"}
BOOL_FALSE = {"0", "false", "no", "n", "нет", "ложь", "f"}
BOOL_EMPTY = {"", "none", "null", "nan"}

CASE_ID_ALIASES = ("case_id", "id", "sample_id", "task_id")
PROMPT_ALIASES = (
    "prompt",
    "input",
    "user_prompt",
    "query",
    "messages",
    "request",
    "rendered_prompt",
    "request_messages",
)
OUTPUT_ALIASES = (
    "model_output",
    "output",
    "response",
    "answer",
    "completion",
    "assistant_response",
    "final_text",
    "response_text",
    "raw_text",
)
CATEGORY_ALIASES = ("category", "attack_category", "family", "family_id", "task_category")
SPLIT_ALIASES = ("split", "subset", "kind", "type", "case_type")
MODEL_ALIASES = ("model", "model_name", "target_model", "runtime_model")
DEFENSE_PROFILE_ALIASES = ("defense_profile", "profile", "defense", "defense_config", "config_name")
DATASET_ALIASES = ("dataset", "dataset_id", "dataset_name", "dataset_path")
STATUS_ALIASES = ("status", "result_status", "case_status")
EXPECTED_ALIASES = ("expected_behavior", "expected_action", "expected", "label", "target_behavior")

ATTACK_SUCCESS_ALIASES = (
    "evaluator_attack_success",
    "attack_success",
    "asr_success",
    "is_attack_success",
    "attack_succeeded",
    "goal_reached",
    "unsafe_success",
    "success_attack",
    "goal_hit",
)
REFUSAL_ALIASES = (
    "evaluator_refusal",
    "refusal",
    "refusal_detected",
    "is_refusal",
    "has_refusal",
    "refused",
)
SAFE_REFUSAL_ALIASES = (
    "evaluator_safe_refusal",
    "safe_refusal",
    "safe_refusal_detected",
    "blocked_attack",
)
FALSE_REFUSAL_ALIASES = (
    "evaluator_false_refusal",
    "false_refusal",
    "fpr_hit",
    "false_positive",
    "benign_refusal",
)
LEAKAGE_ALIASES = (
    "evaluator_leakage",
    "leakage",
    "leakage_detected",
    "exfiltration_detected",
    "system_prompt_leakage",
)
POLICY_VIOLATION_ALIASES = (
    "evaluator_policy_violation",
    "policy_violation",
    "violation_detected",
    "unsafe_output",
)
PARSE_ERROR_ALIASES = ("evaluator_parse_error", "parse_error", "parser_error")

ATTACK_TERMS = (
    "attack",
    "jailbreak",
    "prompt_injection",
    "prompt injection",
    "leakage",
    "exfiltration",
    "format_breaking",
    "format breaking",
    "policy_override",
    "policy override",
    "multistep",
    "obfuscation",
)
BENIGN_TERMS = ("benign", "control", "allowed", "safe")
UTILITY_TERMS = ("utility", "rummlu", "sberquad", "qa", "math", "reasoning")
BORDERLINE_TERMS = ("borderline", "ambiguous", "parse_error", "error", "schema_violation")


@dataclass
class NormalizedAuditCase:
    sample_id: str
    source_file: str
    source_row_index: int
    run_id: Optional[str]
    case_id: str
    model: Optional[str]
    defense_profile: Optional[str]
    dataset: Optional[str]
    split: Optional[str]
    category: Optional[str]
    status: Optional[str]
    is_attack: bool
    is_benign: bool
    is_utility: bool
    is_borderline: bool
    prompt: str
    model_output: str
    expected_behavior: Optional[str]
    evaluator_attack_success: Optional[bool]
    evaluator_refusal: Optional[bool]
    evaluator_safe_refusal: Optional[bool]
    evaluator_false_refusal: Optional[bool]
    evaluator_leakage: Optional[bool]
    evaluator_policy_violation: Optional[bool]
    evaluator_blocked: Optional[bool]
    evaluator_parse_error: Optional[bool]
    evaluator_dlp_hit: Optional[bool]
    evaluator_policy_block: Optional[bool]
    evaluator_schema_violation: Optional[bool]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_blind_row(
        self,
        *,
        redact_secrets: bool,
        max_prompt_chars: int,
        max_output_chars: int,
    ) -> dict[str, Any]:
        prompt = _prepare_text_for_export(
            self.prompt,
            redact_secrets=redact_secrets,
            max_chars=max_prompt_chars,
        )
        output = _prepare_text_for_export(
            self.model_output,
            redact_secrets=redact_secrets,
            max_chars=max_output_chars,
        )
        return {
            "sample_id": self.sample_id,
            "run_id": self.run_id or "",
            "case_id": self.case_id,
            "model": self.model or "",
            "defense_profile": self.defense_profile or "",
            "dataset": self.dataset or "",
            "split": self.split or "",
            "category": self.category or "",
            "status": self.status or "",
            "prompt": prompt,
            "model_output": output,
            "expected_behavior": self.expected_behavior or "",
            "human_attack_success": "",
            "human_refusal": "",
            "human_leakage": "",
            "human_policy_violation": "",
            "human_false_refusal": "",
            "human_ambiguous": "",
            "human_comment": "",
        }

    def to_evaluator_row(self) -> dict[str, Any]:
        row = {
            "not_for_annotation": "technical_evaluator_labels_do_not_use_for_annotation",
        }
        row.update(self.to_dict())
        return row


def discover_case_files(
    *,
    cases_files: Optional[Iterable[Path]] = None,
    runs_dir: Optional[Path] = None,
    glob_pattern: str = "**/cases.jsonl",
) -> list[Path]:
    paths: list[Path] = []
    if cases_files:
        paths.extend(Path(path) for path in cases_files)
    if runs_dir:
        root = Path(runs_dir)
        paths.extend(path for path in root.glob(glob_pattern) if path.is_file())
        for name in CASE_FILE_NAMES - {Path(glob_pattern).name}:
            paths.extend(path for path in root.glob(f"**/{name}") if path.is_file())
    deduped = sorted({path.resolve(): path for path in paths if Path(path).is_file()}.values())
    return deduped


def load_normalized_cases(
    *,
    cases_files: Iterable[Path],
    include_utility: bool = False,
) -> list[NormalizedAuditCase]:
    normalized: list[NormalizedAuditCase] = []
    for case_file in cases_files:
        run_meta = _load_run_metadata(case_file)
        for row_index, row in enumerate(_read_jsonl(case_file), start=1):
            if not isinstance(row, dict):
                continue
            case = normalize_case_row(
                row,
                source_file=case_file,
                source_row_index=row_index,
                run_meta=run_meta,
            )
            if _is_eligible(case, include_utility=include_utility):
                normalized.append(case)
    return normalized


def normalize_case_row(
    row: dict[str, Any],
    *,
    source_file: Path,
    source_row_index: int,
    run_meta: Optional[dict[str, Any]] = None,
) -> NormalizedAuditCase:
    run_meta = run_meta or {}
    run_id = _first_text(row, ("run_id", "run", "run_name")) or _meta_run_id(source_file, run_meta)
    case_id = _first_text(row, CASE_ID_ALIASES) or f"{source_file.stem}-{source_row_index}"
    model = _first_text(row, MODEL_ALIASES) or _meta_model(run_meta)
    defense_profile = _first_text(row, DEFENSE_PROFILE_ALIASES) or _meta_defense_profile(run_meta)
    dataset = _first_text(row, DATASET_ALIASES) or _meta_dataset(run_meta)
    split = _first_text(row, SPLIT_ALIASES) or _meta_split(run_meta)
    category = _first_text(row, CATEGORY_ALIASES)
    status = _first_text(row, STATUS_ALIASES)
    prompt = _first_text(row, PROMPT_ALIASES) or ""
    model_output = _first_text(row, OUTPUT_ALIASES) or ""
    expected = _first_text(row, EXPECTED_ALIASES)

    evaluator_parse_error = _first_bool(row, PARSE_ERROR_ALIASES)
    if evaluator_parse_error is None and status:
        evaluator_parse_error = _contains_any(status, ("parse_error", "parser_error"))

    evaluator_refusal = _first_bool(row, REFUSAL_ALIASES)
    if evaluator_refusal is None:
        predicted_action = _first_text(row, ("predicted_action", "action"))
        if predicted_action:
            evaluator_refusal = predicted_action.lower() == "refuse"

    evaluator_attack_success = _first_bool(row, ATTACK_SUCCESS_ALIASES)
    evaluator_safe_refusal = _first_bool(row, SAFE_REFUSAL_ALIASES)
    evaluator_false_refusal = _first_bool(row, FALSE_REFUSAL_ALIASES)
    evaluator_leakage = _first_bool(row, LEAKAGE_ALIASES)
    evaluator_policy_violation = _first_bool(row, POLICY_VIOLATION_ALIASES)
    evaluator_blocked = _derive_blocked(row, status)
    evaluator_dlp_hit = _derive_dlp_hit(row)
    evaluator_policy_block = _derive_policy_block(row)
    evaluator_schema_violation = _derive_schema_violation(row, status)

    if evaluator_refusal is None or evaluator_attack_success is None or evaluator_false_refusal is None:
        recalculated = _try_recalculate_evaluator(row, model_output, expected)
        if recalculated:
            if evaluator_refusal is None:
                evaluator_refusal = _as_bool(recalculated.get("refused"))
            if evaluator_attack_success is None:
                evaluator_attack_success = _as_bool(recalculated.get("success_attack"))
            if evaluator_safe_refusal is None:
                evaluator_safe_refusal = _as_bool(recalculated.get("blocked_attack"))
            if evaluator_false_refusal is None:
                evaluator_false_refusal = _as_bool(recalculated.get("false_positive"))

    is_attack = _derive_is_attack(row, split, category, expected, evaluator_attack_success)
    is_benign = _derive_is_benign(row, split, category, expected, evaluator_false_refusal)
    is_utility = _derive_is_utility(row, split, category, expected)
    is_borderline = _derive_is_borderline(
        row,
        split=split,
        category=category,
        status=status,
        model_output=model_output,
        evaluator_refusal=evaluator_refusal,
        evaluator_attack_success=evaluator_attack_success,
        evaluator_leakage=evaluator_leakage,
        evaluator_parse_error=evaluator_parse_error,
        evaluator_schema_violation=evaluator_schema_violation,
        evaluator_policy_block=evaluator_policy_block,
    )

    return NormalizedAuditCase(
        sample_id="",
        source_file=str(source_file),
        source_row_index=source_row_index,
        run_id=run_id,
        case_id=str(case_id),
        model=model,
        defense_profile=defense_profile,
        dataset=dataset,
        split=split,
        category=category,
        status=status,
        is_attack=is_attack,
        is_benign=is_benign,
        is_utility=is_utility,
        is_borderline=is_borderline,
        prompt=prompt,
        model_output=model_output,
        expected_behavior=expected,
        evaluator_attack_success=evaluator_attack_success,
        evaluator_refusal=evaluator_refusal,
        evaluator_safe_refusal=evaluator_safe_refusal,
        evaluator_false_refusal=evaluator_false_refusal,
        evaluator_leakage=evaluator_leakage,
        evaluator_policy_violation=evaluator_policy_violation,
        evaluator_blocked=evaluator_blocked,
        evaluator_parse_error=evaluator_parse_error,
        evaluator_dlp_hit=evaluator_dlp_hit,
        evaluator_policy_block=evaluator_policy_block,
        evaluator_schema_violation=evaluator_schema_violation,
    )


def create_audit_sample(
    *,
    cases_files: Optional[Iterable[Path]] = None,
    runs_dir: Optional[Path] = None,
    out_dir: Path,
    glob_pattern: str = "**/cases.jsonl",
    n: int = 250,
    attack_n: Optional[int] = None,
    benign_n: Optional[int] = None,
    borderline_n: Optional[int] = None,
    seed: int = 42,
    redact_secrets: bool = True,
    max_output_chars: int = 6000,
    max_prompt_chars: int = 4000,
    include_utility: bool = False,
    balanced_by: str = "category,defense_profile,model",
    overwrite: bool = False,
) -> dict[str, Any]:
    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()) and not overwrite:
        raise FileExistsError(f"Output directory is not empty: {out_dir}. Use --overwrite.")
    out_dir.mkdir(parents=True, exist_ok=True)

    source_files = discover_case_files(
        cases_files=cases_files,
        runs_dir=runs_dir,
        glob_pattern=glob_pattern,
    )
    if not source_files:
        raise ValueError("No case-level JSONL files found.")

    cases = load_normalized_cases(cases_files=source_files, include_utility=include_utility)
    if not cases:
        raise ValueError("No eligible safety cases found.")

    desired = _desired_bucket_counts(
        n=n,
        attack_n=attack_n,
        benign_n=benign_n,
        borderline_n=borderline_n,
    )
    fields = _parse_group_fields(balanced_by)
    rng = random.Random(seed)
    selected = _select_stratified(cases, desired=desired, balanced_by=fields, rng=rng)
    if n and len(selected) > n and not any(x is not None for x in (attack_n, benign_n, borderline_n)):
        selected = selected[:n]

    selected = _assign_sample_ids(selected)
    audit_id = _build_audit_id(source_files, selected, seed)

    manifest_cases = [
        _manifest_case_dict(
            case,
            redact_secrets=redact_secrets,
            max_prompt_chars=max_prompt_chars,
            max_output_chars=max_output_chars,
        )
        for case in selected
    ]
    manifest = {
        "audit_id": audit_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "source_files": [str(path) for path in source_files],
        "sampling_config": {
            "n": n,
            "attack_n": attack_n,
            "benign_n": benign_n,
            "borderline_n": borderline_n,
            "glob": glob_pattern,
            "include_utility": include_utility,
            "balanced_by": fields,
            "max_prompt_chars": max_prompt_chars,
            "max_output_chars": max_output_chars,
        },
        "selected_sample_ids": [case.sample_id for case in selected],
        "normalized_cases": manifest_cases,
        "evaluator_labels": {
            case.sample_id: {field: getattr(case, field) for field in EVALUATOR_FIELDS}
            for case in selected
        },
        "repo_version": {
            "git_commit": _git_commit_hash(),
        },
        "redaction": {
            "enabled": redact_secrets,
            "method": "project_dlp_or_lightweight_regex",
        },
        "counts": _bucket_counts(selected),
    }

    _write_csv(
        out_dir / "audit_sample_blind.csv",
        BLIND_COLUMNS,
        [
            case.to_blind_row(
                redact_secrets=redact_secrets,
                max_prompt_chars=max_prompt_chars,
                max_output_chars=max_output_chars,
            )
            for case in selected
        ],
    )
    _write_json(out_dir / "audit_manifest.json", manifest)
    evaluator_columns = ["not_for_annotation", *NORMALIZED_FIELDS]
    _write_csv(
        out_dir / "audit_sample_with_evaluator.csv",
        evaluator_columns,
        [case.to_evaluator_row() for case in selected],
    )

    return {
        "audit_id": audit_id,
        "out_dir": str(out_dir),
        "source_files": [str(path) for path in source_files],
        "selected": len(selected),
        "counts": _bucket_counts(selected),
        "files": {
            "blind_csv": str(out_dir / "audit_sample_blind.csv"),
            "manifest": str(out_dir / "audit_manifest.json"),
            "with_evaluator_csv": str(out_dir / "audit_sample_with_evaluator.csv"),
        },
    }


def validate_annotations(
    *,
    annotations_path: Path,
    manifest_path: Path,
    allow_missing: bool = False,
) -> dict[str, Any]:
    manifest = _read_json(manifest_path)
    manifest_cases = _manifest_cases_by_id(manifest)
    rows = _read_csv_rows(annotations_path)
    known_ids = set(manifest_cases)
    seen_ids: set[str] = set()
    invalid_values: list[dict[str, Any]] = []
    unknown_sample_ids: list[str] = []
    missing_required: list[dict[str, Any]] = []
    ambiguous = 0
    annotated = 0

    for row_index, row in enumerate(rows, start=2):
        sample_id = str(row.get("sample_id") or "").strip()
        if not sample_id:
            invalid_values.append({"row": row_index, "field": "sample_id", "value": "", "reason": "missing"})
            continue
        if sample_id not in known_ids:
            unknown_sample_ids.append(sample_id)
            continue
        seen_ids.add(sample_id)
        normalized, row_errors = _normalize_human_row(row, row_index=row_index)
        invalid_values.extend(row_errors)
        if normalized.get("human_ambiguous") is True:
            ambiguous += 1
        if any(normalized.get(field) is not None for field in _human_label_fields()):
            annotated += 1
        missing_required.extend(
            _required_label_warnings(
                row_index=row_index,
                sample_id=sample_id,
                case=manifest_cases[sample_id],
                human=normalized,
            )
        )

    missing_sample_ids = sorted(known_ids - seen_ids)
    summary = {
        "total_rows": len(rows),
        "manifest_samples": len(known_ids),
        "annotated_rows": annotated,
        "ambiguous_rows": ambiguous,
        "missing_required_labels": missing_required,
        "invalid_values": invalid_values,
        "unknown_sample_ids": sorted(set(unknown_sample_ids)),
        "missing_sample_ids": missing_sample_ids,
        "ok": not invalid_values
        and not unknown_sample_ids
        and not missing_sample_ids
        and (allow_missing or not missing_required),
    }
    return summary


def score_annotations(
    *,
    annotations_path: Path,
    manifest_path: Path,
    out_dir: Path,
    exclude_ambiguous: bool = True,
    bootstrap: int = 0,
    seed: int = 42,
    by: str = "category,defense_profile,model",
    min_group_size: int = 10,
    allow_missing: bool = False,
    positive_label: Optional[str] = None,
) -> dict[str, Any]:
    validation = validate_annotations(
        annotations_path=annotations_path,
        manifest_path=manifest_path,
        allow_missing=allow_missing,
    )
    if validation["invalid_values"] or validation["unknown_sample_ids"] or validation["missing_sample_ids"]:
        raise ValueError(f"Invalid annotations: {validation}")
    if validation["missing_required_labels"] and not allow_missing:
        raise ValueError("Missing required labels. Use --allow-missing to score partial annotations.")

    manifest = _read_json(manifest_path)
    manifest_cases = _manifest_cases_by_id(manifest)
    annotations = _read_csv_rows(annotations_path)
    joined = _join_annotations(annotations, manifest_cases)

    task_names = (
        [positive_label] if positive_label else ["attack_success", "refusal", "leakage", "policy_violation", "false_refusal"]
    )
    group_fields = _parse_group_fields(by)
    rng = random.Random(seed)
    metrics_rows: list[dict[str, Any]] = []
    matrix_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []
    warnings: list[str] = []

    for task in task_names:
        if task not in _task_specs():
            warnings.append(f"Unknown task skipped: {task}")
            continue
        task_records, task_warnings = _records_for_task(
            joined,
            task=task,
            exclude_ambiguous=exclude_ambiguous,
        )
        warnings.extend(task_warnings)
        metrics, matrix, errors = _score_record_group(
            task_records,
            task=task,
            group_by="overall",
            group_value="overall",
            bootstrap=bootstrap,
            rng=rng,
        )
        if metrics is not None:
            metrics_rows.append(metrics)
            matrix_rows.append(matrix)
            error_rows.extend(errors)

        for field in group_fields:
            for value, records in _group_records(task_records, field).items():
                if len(records) < min_group_size:
                    continue
                metrics, matrix, errors = _score_record_group(
                    records,
                    task=task,
                    group_by=field,
                    group_value=value,
                    bootstrap=bootstrap,
                    rng=rng,
                )
                if metrics is not None:
                    metrics_rows.append(metrics)
                    matrix_rows.append(matrix)
                    error_rows.extend(errors)

        if "category" in group_fields and "defense_profile" in group_fields:
            for value, records in _group_records(task_records, "category+defense_profile").items():
                if len(records) < min_group_size:
                    continue
                metrics, matrix, errors = _score_record_group(
                    records,
                    task=task,
                    group_by="category+defense_profile",
                    group_value=value,
                    bootstrap=bootstrap,
                    rng=rng,
                )
                if metrics is not None:
                    metrics_rows.append(metrics)
                    matrix_rows.append(matrix)
                    error_rows.extend(errors)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "metrics_summary.csv", _metrics_columns(), metrics_rows)
    _write_json(out_dir / "metrics_summary.json", {"metrics": metrics_rows, "warnings": warnings})
    _write_csv(out_dir / "confusion_matrices.csv", _matrix_columns(), matrix_rows)
    _write_csv(out_dir / "error_cases.csv", _error_columns(), error_rows)
    _write_report(out_dir / "audit_report.md", manifest, validation, metrics_rows, matrix_rows, error_rows, warnings)

    return {
        "out_dir": str(out_dir),
        "metrics_rows": len(metrics_rows),
        "error_cases": len(error_rows),
        "warnings": warnings,
        "files": {
            "metrics_summary_csv": str(out_dir / "metrics_summary.csv"),
            "metrics_summary_json": str(out_dir / "metrics_summary.json"),
            "confusion_matrices_csv": str(out_dir / "confusion_matrices.csv"),
            "error_cases_csv": str(out_dir / "error_cases.csv"),
            "audit_report": str(out_dir / "audit_report.md"),
        },
    }


def _read_jsonl(path: Path) -> Iterable[Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def _load_run_metadata(case_file: Path) -> dict[str, Any]:
    run_config = case_file.parent / "run_config.json"
    if not run_config.exists():
        return {}
    try:
        data = json.loads(run_config.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _meta_run_id(source_file: Path, run_meta: dict[str, Any]) -> Optional[str]:
    return _string_or_none(run_meta.get("run_id")) or source_file.parent.name


def _meta_model(run_meta: dict[str, Any]) -> Optional[str]:
    return _string_or_none(_get_nested(run_meta, ("target", "model"))) or _string_or_none(run_meta.get("model"))


def _meta_defense_profile(run_meta: dict[str, Any]) -> Optional[str]:
    return (
        _string_or_none(_get_nested(run_meta, ("defense", "profile")))
        or _string_or_none(_get_nested(run_meta, ("defense", "config_source_name")))
        or _string_or_none(run_meta.get("defense_profile"))
        or _string_or_none(run_meta.get("config_name"))
    )


def _meta_dataset(run_meta: dict[str, Any]) -> Optional[str]:
    return (
        _string_or_none(run_meta.get("dataset_id"))
        or _string_or_none(run_meta.get("dataset_name"))
        or _string_or_none(run_meta.get("dataset_path"))
    )


def _meta_split(run_meta: dict[str, Any]) -> Optional[str]:
    return _string_or_none(run_meta.get("dataset_split"))


def _get_nested(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _first_text(row: dict[str, Any], aliases: Iterable[str]) -> Optional[str]:
    for alias in aliases:
        if alias not in row:
            continue
        value = row.get(alias)
        text = _value_to_text(value)
        if text != "":
            return text
    return None


def _value_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        rendered = _render_messages(value)
        if rendered:
            return rendered
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, dict):
        rendered = _render_messages([value])
        if rendered:
            return rendered
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _render_messages(value: list[Any]) -> str:
    lines: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            return ""
        role = item.get("role") or item.get("name") or "message"
        content = item.get("content")
        if content is None:
            content = item.get("text")
        lines.append(f"{role}: {_value_to_text(content)}")
    return "\n".join(lines)


def _first_bool(row: dict[str, Any], aliases: Iterable[str]) -> Optional[bool]:
    for alias in aliases:
        if alias in row:
            parsed = _as_bool(row.get(alias))
            if parsed is not None:
                return parsed
    return None


def _as_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and math.isnan(value):
            return None
        return bool(value)
    text = str(value).strip().lower()
    if text in BOOL_EMPTY:
        return None
    if text in BOOL_TRUE:
        return True
    if text in BOOL_FALSE:
        return False
    return None


def _string_or_none(value: Any) -> Optional[str]:
    text = _value_to_text(value)
    return text if text else None


def _contains_any(value: Optional[str], terms: Iterable[str]) -> bool:
    haystack = (value or "").lower()
    return any(term.lower() in haystack for term in terms)


def _derive_blocked(row: dict[str, Any], status: Optional[str]) -> Optional[bool]:
    direct = _first_bool(row, ("evaluator_blocked", "blocked", "blocked_attack", "prefilter_blocked"))
    if direct is not None:
        return direct
    if status and _contains_any(status, ("blocked", "filtered", "force_refusal")):
        return True
    action = _first_text(row, ("prefilter_action", "postfilter_action", "policy_action", "action"))
    if action and _contains_any(action, ("block", "force_refusal", "refuse")):
        return True
    return None


def _derive_dlp_hit(row: dict[str, Any]) -> Optional[bool]:
    direct = _first_bool(row, ("evaluator_dlp_hit", "dlp_hit", "dlp_input_hit", "dlp_output_hit"))
    if direct is not None:
        return direct
    count = row.get("dlp_findings_count")
    if isinstance(count, (int, float)):
        return count > 0
    findings = row.get("dlp_findings")
    if isinstance(findings, list):
        return bool(findings)
    return None


def _derive_policy_block(row: dict[str, Any]) -> Optional[bool]:
    direct = _first_bool(row, ("evaluator_policy_block", "policy_block", "policy_blocked"))
    if direct is not None:
        return direct
    decisions = row.get("policy_decisions")
    if isinstance(decisions, list):
        return any(
            isinstance(item, dict) and str(item.get("action", "")).lower() in {"block", "force_refusal"}
            for item in decisions
        )
    action = _first_text(row, ("policy_action", "policy_decision"))
    if action:
        return action.lower() in {"block", "force_refusal"}
    return None


def _derive_schema_violation(row: dict[str, Any], status: Optional[str]) -> Optional[bool]:
    direct = _first_bool(row, ("evaluator_schema_violation", "schema_violation", "schema_parse_error"))
    if direct is not None:
        return direct
    schema_valid = _as_bool(row.get("schema_valid"))
    if schema_valid is not None:
        return not schema_valid
    if status and _contains_any(status, ("schema_violation", "schema_parse_error")):
        return True
    return None


def _try_recalculate_evaluator(
    row: dict[str, Any],
    model_output: str,
    expected: Optional[str],
) -> Optional[dict[str, Any]]:
    if not model_output or not expected:
        return None
    goal_indicators = row.get("goal_indicators")
    if isinstance(goal_indicators, str):
        goal_indicators = [goal_indicators]
    if goal_indicators is not None and not isinstance(goal_indicators, list):
        goal_indicators = None
    try:
        from bench.core.evaluator import evaluate_case

        return evaluate_case(model_output, expected, goal_indicators)
    except Exception:
        return None


def _derive_is_attack(
    row: dict[str, Any],
    split: Optional[str],
    category: Optional[str],
    expected: Optional[str],
    evaluator_attack_success: Optional[bool],
) -> bool:
    fields = " ".join(
        filter(
            None,
            [
                split,
                category,
                _first_text(row, ("case_type", "type", "kind", "family_id")),
                expected,
            ],
        )
    )
    if _contains_any(fields, ATTACK_TERMS):
        return True
    if expected and expected.lower() in {"safe_refusal", "refuse", "blocked", "block"}:
        return True
    return evaluator_attack_success is not None


def _derive_is_benign(
    row: dict[str, Any],
    split: Optional[str],
    category: Optional[str],
    expected: Optional[str],
    evaluator_false_refusal: Optional[bool],
) -> bool:
    fields = " ".join(
        filter(None, [split, category, _first_text(row, ("case_type", "type", "kind"))])
    )
    if _contains_any(fields, BENIGN_TERMS):
        return True
    if expected and expected.lower() in {"allow", "answer", "comply"}:
        return True
    return evaluator_false_refusal is not None


def _derive_is_utility(
    row: dict[str, Any],
    split: Optional[str],
    category: Optional[str],
    expected: Optional[str],
) -> bool:
    fields = " ".join(
        filter(None, [split, category, _first_text(row, ("case_type", "type", "kind")), expected])
    )
    return _contains_any(fields, UTILITY_TERMS)


def _derive_is_borderline(
    row: dict[str, Any],
    *,
    split: Optional[str],
    category: Optional[str],
    status: Optional[str],
    model_output: str,
    evaluator_refusal: Optional[bool],
    evaluator_attack_success: Optional[bool],
    evaluator_leakage: Optional[bool],
    evaluator_parse_error: Optional[bool],
    evaluator_schema_violation: Optional[bool],
    evaluator_policy_block: Optional[bool],
) -> bool:
    fields = " ".join(filter(None, [split, category, status, _first_text(row, ("case_type", "kind", "type"))]))
    if _contains_any(fields, BORDERLINE_TERMS):
        return True
    if evaluator_parse_error or evaluator_schema_violation:
        return True
    if evaluator_refusal is True and evaluator_leakage is True:
        return True
    if evaluator_refusal is True and evaluator_attack_success is True:
        return True
    if evaluator_policy_block is True and evaluator_attack_success is True:
        return True
    if not str(model_output or "").strip():
        return True
    if not category and not split:
        return True
    return False


def _is_eligible(case: NormalizedAuditCase, *, include_utility: bool) -> bool:
    if case.is_utility and not include_utility and not case.is_borderline:
        return False
    return case.is_attack or case.is_benign or case.is_borderline or (include_utility and case.is_utility)


def _desired_bucket_counts(
    *,
    n: int,
    attack_n: Optional[int],
    benign_n: Optional[int],
    borderline_n: Optional[int],
) -> dict[str, int]:
    if any(value is not None for value in (attack_n, benign_n, borderline_n)):
        return {
            "attack": int(attack_n or 0),
            "benign": int(benign_n or 0),
            "borderline": int(borderline_n or 0),
        }
    attack = int(round(n * 0.7))
    benign = int(round(n * 0.2))
    borderline = max(0, n - attack - benign)
    return {"attack": attack, "benign": benign, "borderline": borderline}


def _select_stratified(
    cases: list[NormalizedAuditCase],
    *,
    desired: dict[str, int],
    balanced_by: list[str],
    rng: random.Random,
) -> list[NormalizedAuditCase]:
    deduped = _dedupe_cases(cases)
    selected: list[NormalizedAuditCase] = []
    selected_keys: set[tuple[str, str]] = set()

    bucketed = {
        "attack": [case for case in deduped if case.is_attack and not case.is_borderline],
        "benign": [case for case in deduped if case.is_benign and not case.is_borderline],
        "borderline": [case for case in deduped if case.is_borderline],
    }
    leftovers: list[NormalizedAuditCase] = []
    for bucket, target in desired.items():
        picked = _balanced_pick(bucketed.get(bucket, []), target, balanced_by=balanced_by, rng=rng)
        for case in picked:
            key = _dedupe_key(case)
            if key in selected_keys:
                continue
            selected.append(case)
            selected_keys.add(key)
        if len(picked) < target:
            leftovers.extend(
                case
                for other_bucket, bucket_cases in bucketed.items()
                if other_bucket != bucket
                for case in bucket_cases
            )

    total_target = sum(desired.values())
    if len(selected) < total_target:
        rng.shuffle(leftovers)
        for case in leftovers:
            key = _dedupe_key(case)
            if key in selected_keys:
                continue
            selected.append(case)
            selected_keys.add(key)
            if len(selected) >= total_target:
                break
    return selected


def _dedupe_cases(cases: list[NormalizedAuditCase]) -> list[NormalizedAuditCase]:
    seen: set[tuple[str, str]] = set()
    out: list[NormalizedAuditCase] = []
    for case in cases:
        key = _dedupe_key(case)
        if key in seen:
            continue
        seen.add(key)
        out.append(case)
    return out


def _dedupe_key(case: NormalizedAuditCase) -> tuple[str, str]:
    run_key = case.run_id or case.source_file
    return (run_key, case.case_id)


def _balanced_pick(
    cases: list[NormalizedAuditCase],
    target: int,
    *,
    balanced_by: list[str],
    rng: random.Random,
) -> list[NormalizedAuditCase]:
    if target <= 0 or not cases:
        return []
    groups: dict[str, list[NormalizedAuditCase]] = {}
    for case in cases:
        key = "|".join(_case_field(case, field) for field in balanced_by) if balanced_by else "all"
        groups.setdefault(key, []).append(case)
    for group_cases in groups.values():
        rng.shuffle(group_cases)
    group_keys = sorted(groups)
    rng.shuffle(group_keys)
    picked: list[NormalizedAuditCase] = []
    while group_keys and len(picked) < target:
        next_keys: list[str] = []
        for key in group_keys:
            group = groups[key]
            if group:
                picked.append(group.pop())
                if len(picked) >= target:
                    break
            if group:
                next_keys.append(key)
        group_keys = next_keys
    return picked


def _assign_sample_ids(cases: list[NormalizedAuditCase]) -> list[NormalizedAuditCase]:
    for index, case in enumerate(cases, start=1):
        case.sample_id = f"AUDIT-{index:06d}"
    return cases


def _parse_group_fields(value: str | Iterable[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = value.split(",")
    else:
        raw = list(value)
    return [item.strip() for item in raw if item and item.strip()]


def _case_field(case: NormalizedAuditCase | dict[str, Any], field: str) -> str:
    if field == "category+defense_profile":
        return f"{_case_field(case, 'category')}|{_case_field(case, 'defense_profile')}"
    if isinstance(case, NormalizedAuditCase):
        value = getattr(case, field, None)
    else:
        value = case.get(field)
    return str(value or "unknown")


def _build_audit_id(source_files: list[Path], selected: list[NormalizedAuditCase], seed: int) -> str:
    material = "|".join([str(seed), *[str(path) for path in source_files], *[case.case_id for case in selected]])
    return "evaluator_audit_" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]


def _manifest_case_dict(
    case: NormalizedAuditCase,
    *,
    redact_secrets: bool,
    max_prompt_chars: int,
    max_output_chars: int,
) -> dict[str, Any]:
    data = case.to_dict()
    data["prompt"] = _prepare_text_for_export(
        case.prompt,
        redact_secrets=redact_secrets,
        max_chars=max_prompt_chars,
    )
    data["model_output"] = _prepare_text_for_export(
        case.model_output,
        redact_secrets=redact_secrets,
        max_chars=max_output_chars,
    )
    return data


def _prepare_text_for_export(text: str, *, redact_secrets: bool, max_chars: int) -> str:
    out = text or ""
    if redact_secrets:
        out = redact_secrets_in_text(out)
    if max_chars and len(out) > max_chars:
        out = out[:max_chars] + "\n[TRUNCATED]"
    return out


def redact_secrets_in_text(text: str) -> str:
    out = text or ""
    try:
        from bench.core.dlp import redact_text, scan_text

        findings = scan_text(out, severity_threshold="low")
        out = redact_text(out, findings)
        out = out.replace("[REDACTED:api_key]", "[REDACTED_API_KEY]")
        out = out.replace("[REDACTED:bearer_token]", "[REDACTED_BEARER_TOKEN]")
        out = out.replace("[REDACTED:jwt]", "[REDACTED_JWT]")
        out = out.replace("[REDACTED:private_key]", "[REDACTED_PRIVATE_KEY]")
        out = out.replace("[REDACTED:secret_assignment]", "[REDACTED_SECRET]")
    except Exception:
        pass
    return _lightweight_redact(out)


def _lightweight_redact(text: str) -> str:
    out = text or ""
    out = re.sub(
        r"-----BEGIN\s+(?:RSA\s+|OPENSSH\s+|EC\s+)?PRIVATE KEY-----[\s\S]+?-----END\s+(?:RSA\s+|OPENSSH\s+|EC\s+)?PRIVATE KEY-----",
        "[REDACTED_PRIVATE_KEY]",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b", "[REDACTED_JWT]", out)
    out = re.sub(r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}\b", "[REDACTED_BEARER_TOKEN]", out)
    out = re.sub(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{12,}\b", "[REDACTED_API_KEY]", out)
    out = re.sub(
        r"\b(password|token|secret|api_key|apikey)\s*[:=]\s*[^\s'\"`]{6,}",
        lambda match: f"{match.group(1)}=[REDACTED_SECRET]",
        out,
        flags=re.IGNORECASE,
    )
    return out


def _bucket_counts(cases: list[NormalizedAuditCase]) -> dict[str, int]:
    return {
        "attack": sum(1 for case in cases if case.is_attack and not case.is_borderline),
        "benign": sum(1 for case in cases if case.is_benign and not case.is_borderline),
        "borderline": sum(1 for case in cases if case.is_borderline),
        "utility": sum(1 for case in cases if case.is_utility),
        "total": len(cases),
    }


def _git_commit_hash() -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        return None
    return None


def _manifest_cases_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases = manifest.get("normalized_cases") or []
    if isinstance(cases, dict):
        return {str(key): value for key, value in cases.items() if isinstance(value, dict)}
    return {
        str(item.get("sample_id")): item
        for item in cases
        if isinstance(item, dict) and item.get("sample_id")
    }


def _normalize_human_row(row: dict[str, Any], *, row_index: int) -> tuple[dict[str, Optional[bool]], list[dict[str, Any]]]:
    normalized: dict[str, Optional[bool]] = {}
    errors: list[dict[str, Any]] = []
    for field in [*_human_label_fields(), "human_ambiguous"]:
        raw = row.get(field, "")
        parsed = _parse_annotation_bool(raw)
        if parsed == "__invalid__":
            errors.append({"row": row_index, "field": field, "value": raw, "reason": "invalid boolean"})
            normalized[field] = None
        elif field == "human_ambiguous" and parsed is None:
            normalized[field] = False
        else:
            normalized[field] = parsed
    return normalized, errors


def _parse_annotation_bool(value: Any) -> Optional[bool] | str:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in BOOL_EMPTY:
        return None
    if text in BOOL_TRUE:
        return True
    if text in BOOL_FALSE:
        return False
    return "__invalid__"


def _human_label_fields() -> list[str]:
    return [
        "human_attack_success",
        "human_refusal",
        "human_leakage",
        "human_policy_violation",
        "human_false_refusal",
    ]


def _required_label_warnings(
    *,
    row_index: int,
    sample_id: str,
    case: dict[str, Any],
    human: dict[str, Optional[bool]],
) -> list[dict[str, Any]]:
    if human.get("human_ambiguous") is True:
        return []
    warnings: list[dict[str, Any]] = []
    if case.get("is_attack") and human.get("human_attack_success") is None:
        warnings.append({"row": row_index, "sample_id": sample_id, "field": "human_attack_success"})
    if case.get("is_benign") and human.get("human_false_refusal") is None:
        warnings.append({"row": row_index, "sample_id": sample_id, "field": "human_false_refusal"})
    if human.get("human_refusal") is None:
        warnings.append({"row": row_index, "sample_id": sample_id, "field": "human_refusal"})
    return warnings


def _join_annotations(rows: list[dict[str, str]], cases_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    joined: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows, start=2):
        sample_id = str(row.get("sample_id") or "").strip()
        case = cases_by_id.get(sample_id)
        if not case:
            continue
        human, _ = _normalize_human_row(row, row_index=row_index)
        item = dict(case)
        item.update(human)
        item["human_comment"] = row.get("human_comment", "")
        item["_row_index"] = row_index
        joined.append(item)
    return joined


def _task_specs() -> dict[str, dict[str, Any]]:
    return {
        "attack_success": {
            "human": "human_attack_success",
            "predictions": ["evaluator_attack_success"],
            "filter": lambda row: bool(row.get("is_attack")),
        },
        "refusal": {
            "human": "human_refusal",
            "predictions": ["evaluator_refusal", "evaluator_safe_refusal"],
            "filter": lambda row: True,
        },
        "leakage": {
            "human": "human_leakage",
            "predictions": ["evaluator_leakage"],
            "filter": lambda row: True,
        },
        "policy_violation": {
            "human": "human_policy_violation",
            "predictions": ["evaluator_policy_violation", "evaluator_attack_success"],
            "filter": lambda row: True,
        },
        "false_refusal": {
            "human": "human_false_refusal",
            "predictions": ["evaluator_false_refusal"],
            "filter": lambda row: bool(row.get("is_benign")),
        },
    }


def _records_for_task(
    rows: list[dict[str, Any]],
    *,
    task: str,
    exclude_ambiguous: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    spec = _task_specs()[task]
    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    missing_prediction = 0
    missing_target = 0
    ambiguous_excluded = 0
    for row in rows:
        if exclude_ambiguous and row.get("human_ambiguous") is True:
            ambiguous_excluded += 1
            continue
        if not spec["filter"](row):
            continue
        target = row.get(spec["human"])
        if target is None:
            missing_target += 1
            continue
        prediction = _first_available_prediction(row, spec["predictions"])
        if prediction is None:
            missing_prediction += 1
            continue
        record = dict(row)
        record["_target"] = bool(target)
        record["_prediction"] = bool(prediction)
        record["_ambiguous_excluded"] = ambiguous_excluded
        record["_missing_excluded"] = missing_prediction + missing_target
        records.append(record)
    if missing_prediction:
        warnings.append(f"{task}: skipped {missing_prediction} rows with missing evaluator prediction")
    if missing_target:
        warnings.append(f"{task}: skipped {missing_target} rows with missing human label")
    return records, warnings


def _first_available_prediction(row: dict[str, Any], fields: list[str]) -> Optional[bool]:
    for field in fields:
        value = row.get(field)
        parsed = _as_bool(value)
        if parsed is not None:
            return parsed
    return None


def _score_record_group(
    records: list[dict[str, Any]],
    *,
    task: str,
    group_by: str,
    group_value: str,
    bootstrap: int,
    rng: random.Random,
) -> tuple[Optional[dict[str, Any]], Optional[dict[str, Any]], list[dict[str, Any]]]:
    if not records:
        return None, None, []
    tp = sum(1 for row in records if row["_target"] and row["_prediction"])
    fp = sum(1 for row in records if not row["_target"] and row["_prediction"])
    fn = sum(1 for row in records if row["_target"] and not row["_prediction"])
    tn = sum(1 for row in records if not row["_target"] and not row["_prediction"])
    values = _metrics_from_counts(tp, fp, fn, tn)
    cis = _bootstrap_cis(records, bootstrap=bootstrap, rng=rng)
    metrics = {
        "task": task,
        "group_by": group_by,
        "group_value": group_value,
        "n": len(records),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": values["precision"],
        "precision_ci_low": cis.get("precision", (None, None))[0],
        "precision_ci_high": cis.get("precision", (None, None))[1],
        "recall": values["recall"],
        "recall_ci_low": cis.get("recall", (None, None))[0],
        "recall_ci_high": cis.get("recall", (None, None))[1],
        "f1": values["f1"],
        "f1_ci_low": cis.get("f1", (None, None))[0],
        "f1_ci_high": cis.get("f1", (None, None))[1],
        "accuracy": values["accuracy"],
        "accuracy_ci_low": cis.get("accuracy", (None, None))[0],
        "accuracy_ci_high": cis.get("accuracy", (None, None))[1],
        "specificity": values["specificity"],
        "positive_support": tp + fn,
        "negative_support": tn + fp,
        "ambiguous_excluded": sum(1 for row in records if row.get("_ambiguous_excluded")),
        "missing_excluded": sum(1 for row in records if row.get("_missing_excluded")),
    }
    matrix = {
        "task": task,
        "group_by": group_by,
        "group_value": group_value,
        "human_positive_pred_positive": tp,
        "human_negative_pred_positive": fp,
        "human_positive_pred_negative": fn,
        "human_negative_pred_negative": tn,
    }
    errors = [_error_row(task, row) for row in records if row["_target"] != row["_prediction"]]
    return metrics, matrix, errors


def _metrics_from_counts(tp: int, fp: int, fn: int, tn: int) -> dict[str, Optional[float]]:
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall) if precision is not None and recall is not None else None
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": _safe_div(tp + tn, tp + fp + fn + tn),
        "specificity": _safe_div(tn, tn + fp),
    }


def _safe_div(num: float, den: float) -> Optional[float]:
    if den == 0:
        return None
    return num / den


def _bootstrap_cis(
    records: list[dict[str, Any]],
    *,
    bootstrap: int,
    rng: random.Random,
) -> dict[str, tuple[Optional[float], Optional[float]]]:
    if bootstrap <= 0 or len(records) < 2:
        return {}
    samples: dict[str, list[float]] = {"precision": [], "recall": [], "f1": [], "accuracy": []}
    for _ in range(bootstrap):
        draw = [records[rng.randrange(len(records))] for _ in range(len(records))]
        tp = sum(1 for row in draw if row["_target"] and row["_prediction"])
        fp = sum(1 for row in draw if not row["_target"] and row["_prediction"])
        fn = sum(1 for row in draw if row["_target"] and not row["_prediction"])
        tn = sum(1 for row in draw if not row["_target"] and not row["_prediction"])
        metrics = _metrics_from_counts(tp, fp, fn, tn)
        for key in samples:
            if metrics[key] is not None:
                samples[key].append(metrics[key])
    return {key: _percentile_ci(values) for key, values in samples.items()}


def _percentile_ci(values: list[float]) -> tuple[Optional[float], Optional[float]]:
    if len(values) < 2:
        return (None, None)
    values = sorted(values)
    low_index = max(0, int(math.floor(0.025 * (len(values) - 1))))
    high_index = min(len(values) - 1, int(math.ceil(0.975 * (len(values) - 1))))
    return (values[low_index], values[high_index])


def _group_records(records: list[dict[str, Any]], field: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in records:
        key = _case_field(row, field)
        grouped.setdefault(key, []).append(row)
    return grouped


def _error_row(task: str, row: dict[str, Any]) -> dict[str, Any]:
    error_type = "FP" if row["_prediction"] and not row["_target"] else "FN"
    return {
        "task": task,
        "error_type": error_type,
        "sample_id": row.get("sample_id", ""),
        "run_id": row.get("run_id", ""),
        "case_id": row.get("case_id", ""),
        "model": row.get("model", ""),
        "defense_profile": row.get("defense_profile", ""),
        "category": row.get("category", ""),
        "prompt": row.get("prompt", ""),
        "model_output": row.get("model_output", ""),
        "evaluator_value": row["_prediction"],
        "human_value": row["_target"],
        "human_comment": row.get("human_comment", ""),
    }


def _metrics_columns() -> list[str]:
    return [
        "task",
        "group_by",
        "group_value",
        "n",
        "tp",
        "fp",
        "fn",
        "tn",
        "precision",
        "precision_ci_low",
        "precision_ci_high",
        "recall",
        "recall_ci_low",
        "recall_ci_high",
        "f1",
        "f1_ci_low",
        "f1_ci_high",
        "accuracy",
        "accuracy_ci_low",
        "accuracy_ci_high",
        "specificity",
        "positive_support",
        "negative_support",
        "ambiguous_excluded",
        "missing_excluded",
    ]


def _matrix_columns() -> list[str]:
    return [
        "task",
        "group_by",
        "group_value",
        "human_positive_pred_positive",
        "human_negative_pred_positive",
        "human_positive_pred_negative",
        "human_negative_pred_negative",
    ]


def _error_columns() -> list[str]:
    return [
        "task",
        "error_type",
        "sample_id",
        "run_id",
        "case_id",
        "model",
        "defense_profile",
        "category",
        "prompt",
        "model_output",
        "evaluator_value",
        "human_value",
        "human_comment",
    ]


def _write_report(
    path: Path,
    manifest: dict[str, Any],
    validation: dict[str, Any],
    metrics_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
    error_rows: list[dict[str, Any]],
    warnings: list[str],
) -> None:
    counts = manifest.get("counts", {})
    overall = [row for row in metrics_rows if row.get("group_by") == "overall"]
    attack_matrix = next(
        (
            row
            for row in matrix_rows
            if row.get("task") == "attack_success" and row.get("group_by") == "overall"
        ),
        None,
    )
    lines = [
        "# Manual Evaluator Audit Report",
        "",
        f"Audit ID: `{manifest.get('audit_id', '')}`",
        f"Sample size: {counts.get('total', validation.get('manifest_samples', 0))}",
        f"Attack: {counts.get('attack', 0)}; benign: {counts.get('benign', 0)}; borderline: {counts.get('borderline', 0)}",
        f"Ambiguous rows in annotations: {validation.get('ambiguous_rows', 0)}",
        "",
        "## Overall Metrics",
        "",
        "| task | n | precision | recall | f1 | accuracy |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in overall:
        lines.append(
            "| {task} | {n} | {precision} | {recall} | {f1} | {accuracy} |".format(
                task=row.get("task"),
                n=row.get("n"),
                precision=_fmt_metric(row.get("precision")),
                recall=_fmt_metric(row.get("recall")),
                f1=_fmt_metric(row.get("f1")),
                accuracy=_fmt_metric(row.get("accuracy")),
            )
        )
    if attack_matrix:
        lines.extend(
            [
                "",
                "## Attack Success Confusion Matrix",
                "",
                f"TP: {attack_matrix.get('human_positive_pred_positive', 0)}; "
                f"FP: {attack_matrix.get('human_negative_pred_positive', 0)}; "
                f"FN: {attack_matrix.get('human_positive_pred_negative', 0)}; "
                f"TN: {attack_matrix.get('human_negative_pred_negative', 0)}",
            ]
        )
    if error_rows:
        lines.extend(["", "## Typical Evaluator Errors", ""])
        for row in error_rows[:10]:
            lines.append(
                f"- {row.get('task')} {row.get('error_type')}: "
                f"{row.get('sample_id')} / {row.get('case_id')} / {row.get('category')}"
            )
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "ASR is a proxy metric from the current evaluator. Manual review estimates evaluator quality "
            "on this control sample and should not be treated as proof that the same quality holds for all "
            "future runs without repeated validation.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _fmt_metric(value: Any) -> str:
    if value is None or value == "":
        return ""
    return f"{float(value):.3f}"
