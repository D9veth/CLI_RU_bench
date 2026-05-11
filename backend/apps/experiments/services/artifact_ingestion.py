import hashlib
import json
import re
from pathlib import Path
from typing import Any

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify

from apps.artifacts.models import RunArtifact
from apps.configs_app.models import DefenseProfile, ModelEndpoint
from apps.datasets.models import Dataset
from apps.experiments.models import BenchmarkRun, RunMetrics


RUN_ROOTS = (
    "runs",
    "runs_matrix",
    "runs_mistral_q5",
    "results",
    "artifacts",
    "runs_web",
)
RUN_MARKERS = ("summary.json", "report.md", "cases.jsonl")
MAX_SEARCH_DEPTH = 4


def get_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "backend").exists() and (parent / "bench").exists():
            return parent
    return current.parents[4]


def find_run_dirs(repo_root: Path) -> list[Path]:
    run_dirs: set[Path] = set()
    for root_name in RUN_ROOTS:
        root = repo_root / root_name
        if not root.exists() or not root.is_dir():
            continue
        for directory in _iter_dirs(root, MAX_SEARCH_DEPTH):
            if _is_run_dir(directory):
                run_dirs.add(directory)
    return sorted(run_dirs)


def parse_run_dir(path: Path) -> dict[str, Any]:
    path = Path(path)
    repo_root = get_repo_root()
    summary = _read_json(path / "summary.json")
    run_config = _read_json(path / "run_config.json")
    preflight = _read_json(path / "preflight.json")
    report_md = _read_text(path / "report.md")

    model_name = _first_text(
        run_config,
        summary,
        paths=(
            ("target", "model"),
            ("target", "model_name"),
            ("model",),
            ("model_name",),
            ("model_endpoint", "model_name"),
        ),
    )
    base_url = _first_text(
        run_config,
        summary,
        paths=(
            ("target", "base_url"),
            ("target", "endpoint_url"),
            ("base_url",),
            ("model_endpoint", "base_url"),
        ),
    )
    provider = _first_text(
        run_config,
        summary,
        paths=(("target", "provider"), ("provider",), ("model_endpoint", "provider")),
    )
    dataset_path = _first_text(
        run_config,
        summary,
        paths=(
            ("dataset_path",),
            ("dataset", "path"),
            ("dataset", "file_path"),
            ("dataset",),
        ),
    )
    dataset_name = _first_text(
        run_config,
        summary,
        paths=(("dataset_name",), ("dataset", "name"), ("dataset_id",)),
    )
    if not dataset_name and dataset_path:
        dataset_name = Path(dataset_path).name

    defense_profile_name = _first_text(
        run_config,
        summary,
        paths=(
            ("defense", "profile"),
            ("defense_profile",),
            ("defense_profile_name",),
            ("config_source_name",),
        ),
    )
    config_source_path = _first_text(run_config, summary, paths=(("config_source_path",),))
    defense_level = _extract_defense_level(
        " ".join(
            part
            for part in (
                defense_profile_name,
                config_source_path,
                str(path),
            )
            if part
        )
    )

    run_id = _first_text(
        run_config,
        summary,
        paths=(("run_id",), ("run", "id"), ("id",)),
    )
    if not run_id:
        run_id = path.name

    status = _infer_status(path, summary, report_md)
    metrics = normalize_metrics(summary, path / "cases.jsonl")
    output_dir = _relative_path(path, repo_root)

    title_parts = [part for part in (model_name, defense_level or defense_profile_name, dataset_name) if part]
    title = " / ".join(title_parts) or run_id

    return {
        "run_id": str(run_id),
        "title": title,
        "status": status,
        "model_name": model_name or "unknown-model",
        "model_endpoint_name": _model_endpoint_name(model_name, base_url, provider),
        "model_base_url": base_url or "",
        "model_provider": _infer_provider(base_url, provider),
        "dataset_name": dataset_name or "Unknown dataset",
        "dataset_path": dataset_path or "",
        "dataset_type": _infer_dataset_type(dataset_path or dataset_name or ""),
        "defense_profile_name": defense_profile_name or defense_level or "Unknown defense profile",
        "defense_level": defense_level or DefenseProfile.Level.CUSTOM,
        "defense_yaml_path": config_source_path or "",
        "output_dir": output_dir,
        "started_at": _parse_datetime(_first_text(run_config, summary, paths=(("started_at",),))),
        "finished_at": _parse_datetime(_first_text(run_config, summary, paths=(("finished_at",),))),
        "summary": summary,
        "run_config": run_config,
        "preflight": preflight,
        "report_md": report_md,
        "metrics": metrics,
        "artifacts": _collect_artifacts(path, repo_root),
    }


@transaction.atomic
def import_run_dir(path: Path, created_by=None) -> BenchmarkRun:
    parsed = parse_run_dir(path)
    run_id = _unique_run_id_for_path(parsed["run_id"], parsed["output_dir"])

    dataset = _get_or_create_dataset(parsed)
    defense_profile = _get_or_create_defense_profile(parsed)
    model_endpoint = _get_or_create_model_endpoint(parsed)

    defaults = {
        "title": parsed["title"],
        "created_by": created_by,
        "model_endpoint": model_endpoint,
        "dataset": dataset,
        "defense_profile": defense_profile,
        "status": parsed["status"],
        "started_at": parsed["started_at"],
        "finished_at": parsed["finished_at"],
        "output_dir": parsed["output_dir"],
        "error_message": _extract_error_message(parsed),
        "config_snapshot_json": {
            "model_endpoint": {
                "name": model_endpoint.name,
                "model_name": model_endpoint.model_name,
                "base_url": model_endpoint.base_url,
            },
            "dataset": {
                "name": dataset.name,
                "file_path": dataset.file_path,
            },
            "defense_profile": {
                "name": defense_profile.name,
                "level": defense_profile.level,
                "yaml_path": defense_profile.yaml_path,
            },
            "source": {
                "output_dir": parsed["output_dir"],
            },
        },
    }
    if created_by is None:
        defaults.pop("created_by")

    run, created = BenchmarkRun.objects.update_or_create(run_id=run_id, defaults=defaults)

    metric_values = parsed["metrics"]
    RunMetrics.objects.update_or_create(run=run, defaults=metric_values)

    for artifact in parsed["artifacts"]:
        RunArtifact.objects.update_or_create(
            run=run,
            file_path=artifact["file_path"],
            defaults={
                "artifact_type": artifact["artifact_type"],
                "size_bytes": artifact["size_bytes"],
            },
        )

    run._ingestion_was_created = created
    run._ingestion_was_updated = not created
    return run


def import_all_runs(repo_root: Path, created_by=None) -> dict[str, Any]:
    run_dirs = find_run_dirs(repo_root)
    summary: dict[str, Any] = {
        "found": len(run_dirs),
        "imported": 0,
        "updated": 0,
        "skipped": 0,
        "errors": [],
    }
    for run_dir in run_dirs:
        try:
            run = import_run_dir(run_dir, created_by=created_by)
        except Exception as exc:  # pragma: no cover - error content is surfaced to caller.
            summary["skipped"] += 1
            summary["errors"].append({"path": str(run_dir), "error": str(exc)})
            continue
        if getattr(run, "_ingestion_was_created", False):
            summary["imported"] += 1
        else:
            summary["updated"] += 1
    return summary


@transaction.atomic
def import_artifacts_for_existing_run(run: BenchmarkRun, path: Path) -> BenchmarkRun:
    parsed = parse_run_dir(path)
    metric_values = parsed["metrics"]
    RunMetrics.objects.update_or_create(run=run, defaults=metric_values)

    for artifact in parsed["artifacts"]:
        RunArtifact.objects.update_or_create(
            run=run,
            file_path=artifact["file_path"],
            defaults={
                "artifact_type": artifact["artifact_type"],
                "size_bytes": artifact["size_bytes"],
            },
        )

    updates = {
        "output_dir": parsed["output_dir"],
        "error_message": _extract_error_message(parsed),
    }
    if parsed["finished_at"]:
        updates["finished_at"] = parsed["finished_at"]
    _update_if_changed(run, updates)
    return run


def normalize_metrics(summary: dict[str, Any], cases_path: Path | None = None) -> dict[str, Any]:
    safety = summary.get("safety") if isinstance(summary.get("safety"), dict) else {}
    utility = summary.get("utility") if isinstance(summary.get("utility"), dict) else {}

    proxy_asr = _metric_value(
        summary,
        ("proxy_asr", "asr", "ASR", "attack_success_rate", "attack_success_rate_proxy"),
        preferred_sections=(safety,),
    )
    one_minus_asr = _metric_value(
        summary,
        ("one_minus_asr", "1-ASR", "robustness"),
        preferred_sections=(safety,),
    )
    if one_minus_asr is None and proxy_asr is not None:
        one_minus_asr = 1 - proxy_asr

    total_cases = _int_metric(summary, ("total_cases",), default=None)
    status_counts = summary.get("status_counts")
    if not isinstance(status_counts, dict):
        status_counts = summary.get("counts_by_status")
    if not isinstance(status_counts, dict):
        status_counts = {}

    ok_cases = _int_metric(summary, ("ok_cases",), default=None)
    error_cases = _int_metric(summary, ("error_cases",), default=None)
    if ok_cases is None:
        ok_cases = _safe_int(status_counts.get("ok"))
    if error_cases is None:
        error_cases = _safe_int(status_counts.get("error"), 0) + _safe_int(
            status_counts.get("parse_error"), 0
        )

    if total_cases is None:
        total_cases = _count_cases(cases_path) if cases_path else 0
    if ok_cases is None:
        ok_cases = 0
    if error_cases is None:
        error_cases = 0

    parse_error_rate = _metric_value(
        summary,
        ("parse_error_rate", "parse_error", "parse_errors"),
    )
    parse_errors = _metric_value(summary, ("parse_errors",))
    if parse_error_rate is not None and parse_error_rate > 1 and total_cases:
        parse_error_rate = parse_error_rate / total_cases
    if parse_error_rate is None and parse_errors is not None and total_cases:
        parse_error_rate = parse_errors / total_cases

    return {
        "proxy_asr": proxy_asr,
        "one_minus_asr": one_minus_asr,
        "tpr": _metric_value(summary, ("tpr", "TPR"), preferred_sections=(safety,)),
        "fpr": _metric_value(
            summary,
            ("fpr", "FPR", "false_positive_rate"),
            preferred_sections=(safety,),
        ),
        "u_mean": _metric_value(
            summary,
            ("u_mean", "U_mean", "utility_mean", "utility", "U"),
            preferred_sections=(utility,),
        ),
        "rummlu_accuracy": _metric_value(
            summary,
            ("rummlu_accuracy", "ruMMLU", "rummlu", "accuracy"),
            preferred_sections=(utility,),
        ),
        "sberquad_f1": _metric_value(
            summary,
            ("sberquad_f1", "SberQuAD_F1", "sberquad", "f1"),
            preferred_sections=(utility,),
        ),
        "sberquad_em": _metric_value(
            summary,
            ("sberquad_em", "SberQuAD_EM", "em"),
            preferred_sections=(utility,),
        ),
        "p50_latency": _metric_value(
            summary,
            ("p50_latency", "latency_p50", "p50", "latency_ms_p50"),
            preferred_sections=(safety, utility),
        ),
        "p95_latency": _metric_value(
            summary,
            ("p95_latency", "latency_p95", "p95", "latency_ms_p95"),
            preferred_sections=(safety, utility),
        ),
        "parse_error_rate": parse_error_rate,
        "total_cases": total_cases or 0,
        "ok_cases": ok_cases or 0,
        "error_cases": error_cases or 0,
    }


def _iter_dirs(root: Path, max_depth: int):
    yield root
    root_depth = len(root.parts)
    stack = [root]
    while stack:
        current = stack.pop()
        depth = len(current.parts) - root_depth
        if depth >= max_depth:
            continue
        try:
            children = [child for child in current.iterdir() if child.is_dir()]
        except OSError:
            continue
        stack.extend(children)
        for child in children:
            yield child


def _is_run_dir(path: Path) -> bool:
    return any((path / marker).is_file() for marker in RUN_MARKERS)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _relative_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def _first_text(*sources: dict[str, Any], paths: tuple[tuple[str, ...], ...]) -> str:
    for source in sources:
        for path in paths:
            value = _deep_get(source, path)
            if value not in (None, ""):
                return str(value)
    return ""


def _deep_get(data: Any, path: tuple[str, ...]) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _metric_value(
    data: dict[str, Any],
    keys: tuple[str, ...],
    preferred_sections: tuple[dict[str, Any], ...] = (),
) -> float | None:
    for section in preferred_sections:
        value = _find_key(section, keys, recursive=False)
        number = _safe_float(value)
        if number is not None:
            return number
    value = _find_key(data, keys, recursive=True)
    return _safe_float(value)


def _int_metric(data: dict[str, Any], keys: tuple[str, ...], default: int | None = 0) -> int | None:
    value = _find_key(data, keys, recursive=True)
    parsed = _safe_int(value)
    return default if parsed is None else parsed


def _find_key(data: Any, keys: tuple[str, ...], recursive: bool = True) -> Any:
    if not isinstance(data, dict):
        return None
    lower_keys = {key.lower(): key for key in keys}
    for key, value in data.items():
        if key.lower() in lower_keys and not isinstance(value, (dict, list)):
            return value
    if recursive:
        for value in data.values():
            if isinstance(value, dict):
                found = _find_key(value, keys, recursive=True)
                if found is not None:
                    return found
    return None


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any, default: int | None = None) -> int | None:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _count_cases(cases_path: Path | None) -> int:
    if not cases_path or not cases_path.is_file():
        return 0
    try:
        with cases_path.open("r", encoding="utf-8") as file:
            return sum(1 for line in file if line.strip())
    except OSError:
        return 0


def _infer_dataset_type(value: str) -> str:
    lowered = value.lower()
    if "pilot" in lowered:
        return Dataset.DatasetType.PILOT
    if "sample" in lowered:
        return Dataset.DatasetType.SAMPLE
    if "big" in lowered or "merged" in lowered:
        return Dataset.DatasetType.FULL
    if "generated" in lowered or "/gen" in lowered:
        return Dataset.DatasetType.GENERATED
    return Dataset.DatasetType.UNKNOWN


def _extract_defense_level(value: str) -> str:
    match = re.search(r"(?i)(?:^|[^a-z0-9])(D[0-3])(?:[^a-z0-9]|$)", value)
    return match.group(1).upper() if match else ""


def _infer_provider(base_url: str, provider: str = "") -> str:
    source = f"{base_url} {provider}".lower()
    if "localhost:1234" in source or "lmstudio" in source or "lm studio" in source:
        return ModelEndpoint.Provider.LMSTUDIO
    if "ollama" in source:
        return ModelEndpoint.Provider.OLLAMA
    if "openai" in source or "compatible" in source:
        return ModelEndpoint.Provider.OPENAI_COMPATIBLE
    return ModelEndpoint.Provider.OTHER


def _model_endpoint_name(model_name: str, base_url: str, provider: str) -> str:
    inferred_provider = _infer_provider(base_url, provider)
    if inferred_provider == ModelEndpoint.Provider.LMSTUDIO:
        return "Local LM Studio"
    if model_name:
        return model_name
    return "Unknown model endpoint"


def _infer_status(path: Path, summary: dict[str, Any], report_md: str) -> str:
    status = _first_text(summary, paths=(("status",),))
    if status in BenchmarkRun.Status.values:
        return status
    if _has_error_log(path):
        return BenchmarkRun.Status.FAILED
    if summary or report_md:
        return BenchmarkRun.Status.COMPLETED
    return BenchmarkRun.Status.COMPLETED


def _has_error_log(path: Path) -> bool:
    for file_path in path.glob("*.log"):
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        if "error" in text or "exception" in text or "traceback" in text:
            return True
    return False


def _parse_datetime(value: str):
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _collect_artifacts(path: Path, repo_root: Path) -> list[dict[str, Any]]:
    artifacts = []
    for file_path in sorted(path.iterdir()):
        if not file_path.is_file():
            continue
        artifact_type = _artifact_type_for(file_path)
        if artifact_type is None:
            continue
        artifacts.append(
            {
                "artifact_type": artifact_type,
                "file_path": _relative_path(file_path, repo_root),
                "size_bytes": file_path.stat().st_size,
            }
        )
    return artifacts


def _artifact_type_for(path: Path) -> str | None:
    name = path.name
    suffix = path.suffix.lower()
    exact = {
        "run_config.json": RunArtifact.ArtifactType.RUN_CONFIG,
        "preflight.json": RunArtifact.ArtifactType.PREFLIGHT,
        "cases.jsonl": RunArtifact.ArtifactType.CASES,
        "summary.json": RunArtifact.ArtifactType.SUMMARY,
        "report.md": RunArtifact.ArtifactType.REPORT,
    }
    if name in exact:
        return exact[name]
    if suffix == ".csv":
        return RunArtifact.ArtifactType.CSV
    if suffix in {".png", ".jpg", ".jpeg", ".svg"}:
        return RunArtifact.ArtifactType.FIGURE
    if suffix in {".log", ".txt"}:
        return RunArtifact.ArtifactType.LOG
    return None


def _unique_run_id_for_path(run_id: str, output_dir: str) -> str:
    existing = BenchmarkRun.objects.filter(run_id=run_id).first()
    if existing is None or existing.output_dir == output_dir:
        return run_id
    path_hash = hashlib.sha1(output_dir.encode("utf-8")).hexdigest()[:8]
    return f"{run_id}_{path_hash}"[:64]


def _get_or_create_dataset(parsed: dict[str, Any]) -> Dataset:
    file_path = parsed["dataset_path"] or parsed["output_dir"]
    name = parsed["dataset_name"] or Path(file_path).name or "Unknown dataset"
    slug = _stable_slug(name, file_path)
    dataset, _ = Dataset.objects.get_or_create(
        slug=slug,
        defaults={
            "name": name[:255],
            "description": "Imported from CLI artifacts.",
            "file_path": file_path,
            "dataset_type": parsed["dataset_type"],
            "total_cases": parsed["metrics"]["total_cases"],
        },
    )
    updates = {
        "name": name[:255],
        "file_path": file_path,
        "dataset_type": parsed["dataset_type"],
        "total_cases": max(dataset.total_cases, parsed["metrics"]["total_cases"]),
    }
    _update_if_changed(dataset, updates)
    return dataset


def _get_or_create_defense_profile(parsed: dict[str, Any]) -> DefenseProfile:
    level = parsed["defense_level"]
    name = parsed["defense_profile_name"] or level or "Unknown defense profile"
    slug_source = level.lower() if level in {"D0", "D1", "D2", "D3"} else name
    slug = _stable_slug(slug_source, parsed["defense_yaml_path"] or parsed["output_dir"])
    profile, _ = DefenseProfile.objects.get_or_create(
        slug=slug,
        defaults={
            "name": name[:255],
            "level": level,
            "description": "Imported from CLI artifacts.",
            "yaml_path": parsed["defense_yaml_path"],
        },
    )
    updates = {
        "name": name[:255],
        "level": level,
        "yaml_path": parsed["defense_yaml_path"] or profile.yaml_path,
    }
    _update_if_changed(profile, updates)
    return profile


def _get_or_create_model_endpoint(parsed: dict[str, Any]) -> ModelEndpoint:
    model_name = parsed["model_name"] or "unknown-model"
    base_url = parsed["model_base_url"] or "http://unknown.local"
    name = parsed["model_endpoint_name"] or model_name
    slug = _stable_slug(name, f"{model_name}-{base_url}")
    endpoint, _ = ModelEndpoint.objects.get_or_create(
        slug=slug,
        defaults={
            "name": name[:255],
            "provider": parsed["model_provider"],
            "model_name": model_name[:255],
            "base_url": base_url,
        },
    )
    updates = {
        "name": name[:255],
        "provider": parsed["model_provider"],
        "model_name": model_name[:255],
        "base_url": base_url,
    }
    _update_if_changed(endpoint, updates)
    return endpoint


def _stable_slug(name: str, fallback: str) -> str:
    base = slugify(name)[:42]
    if not base:
        base = "imported"
    digest = hashlib.sha1(fallback.encode("utf-8")).hexdigest()[:7]
    return f"{base}-{digest}"[:50]


def _update_if_changed(instance, updates: dict[str, Any]) -> None:
    changed_fields = []
    for field, value in updates.items():
        if getattr(instance, field) != value:
            setattr(instance, field, value)
            changed_fields.append(field)
    if changed_fields:
        if hasattr(instance, "updated_at"):
            changed_fields.append("updated_at")
        instance.save(update_fields=changed_fields)


def _extract_error_message(parsed: dict[str, Any]) -> str:
    error_message = _first_text(parsed["summary"], parsed["preflight"], paths=(("error_message",), ("error",)))
    return error_message[:1000]
