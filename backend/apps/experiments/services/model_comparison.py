import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from apps.artifacts.models import RunArtifact
from apps.experiments.models import BenchmarkRun
from apps.experiments.serializers import _model_display_name
from apps.experiments.services.artifact_ingestion import get_repo_root


class MetricsMissingError(ValueError):
    pass


LOWER_IS_BETTER = {
    "proxy_asr",
    "fpr",
    "p50_latency",
    "p95_latency",
    "parse_error_rate",
}
HIGHER_IS_BETTER = {
    "one_minus_asr",
    "u_mean",
    "rummlu_accuracy",
    "sberquad_f1",
    "sberquad_em",
}

METRIC_DEFINITIONS = (
    ("proxy_asr", "proxy-ASR", "lower"),
    ("one_minus_asr", "1−proxy-ASR", "higher"),
    ("fpr", "FPR", "lower"),
    ("u_mean", "U_mean", "higher"),
    ("rummlu_accuracy", "ruMMLU accuracy", "higher"),
    ("sberquad_f1", "SberQuAD F1", "higher"),
    ("sberquad_em", "SberQuAD EM", "higher"),
    ("p50_latency", "p50 latency", "lower"),
    ("p95_latency", "p95 latency", "lower"),
    ("parse_error_rate", "parse error rate", "lower"),
    ("total_cases", "total cases", "neutral"),
)


def compare_runs(run_a: BenchmarkRun, run_b: BenchmarkRun) -> dict:
    metrics_a = _run_metrics(run_a)
    metrics_b = _run_metrics(run_b)
    if metrics_a is None or metrics_b is None:
        raise MetricsMissingError("У одного из запусков нет рассчитанных метрик. Сравнение невозможно.")

    metric_rows = []
    deltas = {}
    winner_by_metric = {}
    for key, label, direction in METRIC_DEFINITIONS:
        value_a = _metric_value(metrics_a, key)
        value_b = _metric_value(metrics_b, key)
        delta = _delta(value_a, value_b)
        better = _winner(value_a, value_b, direction)
        metric_rows.append(
            {
                "key": key,
                "label": label,
                "value_a": value_a,
                "value_b": value_b,
                "delta": delta,
                "better": better,
                "direction": direction,
            }
        )
        deltas[key] = delta
        winner_by_metric[key] = better

    return {
        "run_a": _run_summary(run_a),
        "run_b": _run_summary(run_b),
        "model_a": _model_display_name(run_a.model_endpoint),
        "model_b": _model_display_name(run_b.model_endpoint),
        "dataset_a": run_a.dataset.name,
        "dataset_b": run_b.dataset.name,
        "defense_profile_a": run_a.defense_profile.name,
        "defense_profile_b": run_b.defense_profile.name,
        "metrics": metric_rows,
        "deltas": deltas,
        "winner_by_metric": winner_by_metric,
        "warnings": _warnings(run_a, run_b, metrics_a, metrics_b),
    }


def compare_runs_by_categories(run_a: BenchmarkRun, run_b: BenchmarkRun) -> list[dict]:
    cases_a = _read_cases(run_a)
    cases_b = _read_cases(run_b)
    if not cases_a or not cases_b:
        return []

    aggregated_a = _category_proxy_asr(cases_a)
    aggregated_b = _category_proxy_asr(cases_b)
    if not aggregated_a or not aggregated_b:
        return []

    rows = []
    for category in sorted(set(aggregated_a) | set(aggregated_b)):
        value_a = aggregated_a.get(category)
        value_b = aggregated_b.get(category)
        delta = _delta(value_a, value_b)
        rows.append(
            {
                "category": category,
                "proxy_asr_a": value_a,
                "proxy_asr_b": value_b,
                "delta": delta,
                "better": _winner(value_a, value_b, "lower"),
            }
        )
    return rows


def top_different_cases(run_a: BenchmarkRun, run_b: BenchmarkRun, limit=10) -> list[dict]:
    cases_a = _cases_by_id(_read_cases(run_a))
    cases_b = _cases_by_id(_read_cases(run_b))
    if not cases_a or not cases_b:
        return []

    rows = []
    for case_id in sorted(set(cases_a) & set(cases_b)):
        case_a = cases_a[case_id]
        case_b = cases_b[case_id]
        signature_a = _case_signature(case_a)
        signature_b = _case_signature(case_b)
        if not signature_a or not signature_b or signature_a == signature_b:
            continue

        better = _case_winner(case_a, case_b)
        rows.append(
            {
                "case_id": case_id,
                "category": _case_category(case_a) or _case_category(case_b) or "",
                "result_a": _case_result(case_a),
                "result_b": _case_result(case_b),
                "better": better,
                "difference": _difference_label(better),
            }
        )
        if len(rows) >= limit:
            break
    return rows


def _run_metrics(run: BenchmarkRun):
    try:
        return run.metrics
    except BenchmarkRun.metrics.RelatedObjectDoesNotExist:
        return None


def _metric_value(metrics, key: str):
    value = getattr(metrics, key, None)
    if key == "total_cases":
        return int(value) if value is not None else None
    return float(value) if isinstance(value, (int, float)) else value


def _delta(value_a, value_b):
    if value_a is None or value_b is None:
        return None
    return float(value_a) - float(value_b)


def _winner(value_a, value_b, direction: str):
    if value_a is None or value_b is None or direction == "neutral":
        return None
    if abs(float(value_a) - float(value_b)) <= 1e-12:
        return "equal"
    if direction == "lower":
        return "a" if value_a < value_b else "b"
    return "a" if value_a > value_b else "b"


def _warnings(run_a: BenchmarkRun, run_b: BenchmarkRun, metrics_a, metrics_b) -> list[dict]:
    warnings = []
    if run_a.dataset_id != run_b.dataset_id:
        warnings.append(
            {
                "code": "different_dataset",
                "message": "Запуски выполнены на разных датасетах.",
            }
        )
    if run_a.defense_profile_id != run_b.defense_profile_id:
        warnings.append(
            {
                "code": "different_defense_profile",
                "message": "Запуски выполнены с разными профилями защиты.",
            }
        )
    if metrics_a.total_cases != metrics_b.total_cases:
        warnings.append(
            {
                "code": "different_total_cases",
                "message": "У запусков разное количество кейсов.",
            }
        )
    return warnings


def _run_summary(run: BenchmarkRun) -> dict:
    return {
        "id": run.id,
        "run_id": run.run_id,
        "title": run.title,
        "model": _model_display_name(run.model_endpoint),
        "model_endpoint": run.model_endpoint_id,
        "dataset": run.dataset.name,
        "dataset_id": run.dataset_id,
        "profile": run.defense_profile.name,
        "defense_profile": run.defense_profile_id,
        "status": run.status,
        "created_at": run.created_at,
        "finished_at": run.finished_at,
    }


def _read_cases(run: BenchmarkRun) -> list[dict]:
    path = _cases_path(run)
    if path is None or not path.is_file():
        return []

    cases = []
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    return []
                if isinstance(row, dict):
                    cases.append(row)
    except OSError:
        return []
    return cases


def _cases_path(run: BenchmarkRun) -> Path | None:
    artifact = (
        RunArtifact.objects.filter(run=run, artifact_type=RunArtifact.ArtifactType.CASES)
        .order_by("id")
        .first()
    )
    if artifact is None:
        artifact = RunArtifact.objects.filter(run=run, file_path__iendswith="cases.jsonl").order_by("id").first()
    if artifact is not None:
        return _resolve_path(artifact.file_path)

    if run.output_dir:
        return _resolve_path(str(Path(run.output_dir) / "cases.jsonl"))
    return None


def _resolve_path(file_path: str) -> Path:
    path = Path(file_path)
    if path.is_absolute():
        return path
    return get_repo_root() / path


def _category_proxy_asr(cases: list[dict]) -> dict[str, float]:
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"success": 0, "total": 0})
    for row in cases:
        if not _is_attack_row(row):
            continue
        category = _case_category(row)
        success = _proxy_success(row)
        if not category or success is None:
            continue
        buckets[category]["total"] += 1
        if success:
            buckets[category]["success"] += 1
    return {
        category: values["success"] / values["total"]
        for category, values in buckets.items()
        if values["total"]
    }


def _is_attack_row(row: dict) -> bool:
    if "success_attack" in row or "blocked_attack" in row:
        return True
    case_type = _text(row.get("case_type") or row.get("type") or row.get("kind") or row.get("task_type"))
    expected_action = _text(row.get("expected_action"))
    return case_type == "attack" or expected_action in {"safe_refusal", "refuse"}


def _case_category(row: dict) -> str:
    for key in ("category", "kind", "task_type", "case_type", "type"):
        value = _text(row.get(key))
        if value:
            return value
    return ""


def _proxy_success(row: dict) -> bool | None:
    value = row.get("success_attack")
    if isinstance(value, bool):
        return value
    value = row.get("blocked_attack")
    if isinstance(value, bool):
        return not value
    value = row.get("goal_hit")
    if isinstance(value, bool) and value:
        return True
    value = row.get("success")
    if isinstance(value, bool):
        return value
    status = _text(row.get("status") or row.get("verdict") or row.get("result"))
    if status in {"goal_hit", "attack_success", "success_attack", "leaked"}:
        return True
    if status in {"refused", "safe", "blocked", "filtered_prefilter", "filtered_postfilter"}:
        return False
    score = _number(row.get("score"))
    if score is not None:
        return score > 0
    return None


def _cases_by_id(cases: list[dict]) -> dict[str, dict]:
    indexed = {}
    for row in cases:
        case_id = row.get("case_id", row.get("id"))
        if case_id is None:
            continue
        indexed.setdefault(str(case_id), row)
    return indexed


def _case_signature(row: dict) -> tuple[Any, ...]:
    values = []
    for key in (
        "verdict",
        "result",
        "status",
        "predicted_action",
        "success_attack",
        "blocked_attack",
        "false_positive",
        "goal_hit",
        "score",
        "utility_score",
    ):
        if key in row:
            values.append(row.get(key))
    return tuple(values)


def _case_result(row: dict) -> str:
    status = _text(row.get("status"))
    if status == "parse_error":
        return "parse_error"
    if row.get("success_attack") is True:
        return "goal_hit" if row.get("goal_hit") is True else "attack_success"
    if row.get("success_attack") is False:
        return "refused" if row.get("blocked_attack") is True or row.get("refused") is True else "safe"
    if row.get("false_positive") is True:
        return "false_positive"
    if row.get("true_negative") is True:
        return "safe"
    for key in ("verdict", "result", "status", "predicted_action"):
        value = _text(row.get(key))
        if value:
            return value
    score = _number(row.get("utility_score", row.get("score")))
    if score is not None:
        return f"score={score:.3f}"
    return "unknown"


def _case_winner(case_a: dict, case_b: dict) -> str | None:
    score_a = _number(case_a.get("utility_score", case_a.get("score")))
    score_b = _number(case_b.get("utility_score", case_b.get("score")))
    if not _is_attack_row(case_a) and not _is_attack_row(case_b) and score_a is not None and score_b is not None:
        return _winner(score_a, score_b, "higher")

    risk_a = _case_risk(case_a)
    risk_b = _case_risk(case_b)
    if risk_a is None or risk_b is None:
        return None
    return _winner(risk_a, risk_b, "lower")


def _case_risk(row: dict) -> float | None:
    status = _text(row.get("status"))
    if status == "parse_error":
        return 3.0
    if row.get("success_attack") is True or row.get("goal_hit") is True:
        return 2.0
    if row.get("false_positive") is True:
        return 1.5
    if row.get("blocked_attack") is True or row.get("true_negative") is True:
        return 0.0
    if row.get("refused") is True:
        return 0.5
    proxy_success = _proxy_success(row) if _is_attack_row(row) else None
    if proxy_success is not None:
        return 2.0 if proxy_success else 0.0
    return None


def _difference_label(better: str | None) -> str:
    if better == "a":
        return "лучше A"
    if better == "b":
        return "лучше B"
    if better == "equal":
        return "одинаково"
    return "разные значения"


def _number(value) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _text(value) -> str:
    return str(value).strip() if value not in (None, "") else ""
