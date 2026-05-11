import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterator

from django.db import transaction

from apps.artifacts.models import ProjectArtifact
from apps.configs_app.models import DefenseProfile
from apps.datasets.models import Dataset
from apps.experiments.models import BenchmarkRun


SCAN_ROOTS = (
    "data",
    "configs",
    "runs",
    "runs_matrix",
    "runs_mistral_q5",
    "runs_web",
    "results",
    "artifacts",
    "docs",
    "scripts",
)
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}
TEXT_EXTENSIONS = {
    ".csv",
    ".json",
    ".jsonl",
    ".log",
    ".md",
    ".py",
    ".sh",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
}
KNOWN_EXTENSIONS = TEXT_EXTENSIONS | {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".docx"}
MAX_UNKNOWN_BINARY_SIZE = 5 * 1024 * 1024
MAX_PARSE_BYTES = 5 * 1024 * 1024


def get_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "backend").exists() and (parent / "bench").exists():
            return parent
    return current.parents[4]


def iter_candidate_files(repo_root: Path) -> Iterator[Path]:
    repo_root = Path(repo_root).resolve()
    for root_name in SCAN_ROOTS:
        root = repo_root / root_name
        if not root.is_dir():
            continue
        yield from _walk_files(root, repo_root)


def classify_artifact(path: Path, repo_root: Path) -> str:
    relative = _relative_path(path, repo_root)
    parts = relative.parts
    source_dir = parts[0] if parts else ""
    suffix = path.suffix.lower()
    name = path.name.lower()

    if source_dir == "data" and suffix in {".jsonl", ".json", ".yaml", ".yml"}:
        return ProjectArtifact.ArtifactType.DATASET
    if source_dir == "configs" and suffix in {".yaml", ".yml", ".json"}:
        return ProjectArtifact.ArtifactType.CONFIG
    if name in {"summary.json", "run_config.json", "preflight.json", "cases.jsonl", "report.md"}:
        return ProjectArtifact.ArtifactType.RUN_ARTIFACT
    if suffix == ".md":
        return ProjectArtifact.ArtifactType.REPORT if "report" in path.stem.lower() else ProjectArtifact.ArtifactType.MARKDOWN
    if suffix == ".csv":
        return ProjectArtifact.ArtifactType.TABLE
    if suffix in {".png", ".jpg", ".jpeg", ".svg"}:
        return ProjectArtifact.ArtifactType.FIGURE
    if suffix == ".json":
        return ProjectArtifact.ArtifactType.JSON
    if suffix == ".jsonl":
        return ProjectArtifact.ArtifactType.JSONL
    if suffix == ".log":
        return ProjectArtifact.ArtifactType.LOG
    if suffix in {".py", ".sh"}:
        return ProjectArtifact.ArtifactType.SCRIPT
    if suffix in {".pdf", ".docx"}:
        return ProjectArtifact.ArtifactType.DOCUMENT
    return ProjectArtifact.ArtifactType.OTHER


def compute_file_metadata(path: Path, repo_root: Path) -> dict[str, Any]:
    stat = path.stat()
    relative = _relative_path(path, repo_root)
    source_dir = relative.parts[0] if relative.parts else ""
    suffix = path.suffix.lower()
    artifact_type = classify_artifact(path, repo_root)
    line_count = _count_lines(path) if _is_text_file(path) else None
    metadata_json = {
        "relative_path": str(relative),
        "content_type": artifact_type,
    }
    metadata_json.update(_inspect_file(path, suffix, line_count))

    return {
        "name": path.name,
        "artifact_type": artifact_type,
        "file_path": str(relative),
        "source_dir": source_dir,
        "extension": suffix.lstrip("."),
        "size_bytes": stat.st_size,
        "line_count": line_count,
        "sha256": _sha256(path),
        "metadata_json": metadata_json,
    }


@transaction.atomic
def import_project_artifact(path: Path, repo_root: Path) -> ProjectArtifact:
    metadata = compute_file_metadata(path, repo_root)
    related = _related_objects(metadata["file_path"], repo_root)
    defaults = {
        "name": metadata["name"],
        "artifact_type": metadata["artifact_type"],
        "source_dir": metadata["source_dir"],
        "extension": metadata["extension"],
        "size_bytes": metadata["size_bytes"],
        "line_count": metadata["line_count"],
        "sha256": metadata["sha256"],
        "metadata_json": metadata["metadata_json"],
        **related,
    }
    artifact, created = ProjectArtifact.objects.update_or_create(
        file_path=metadata["file_path"],
        defaults=defaults,
    )
    artifact._ingestion_was_created = created
    artifact._ingestion_was_updated = not created
    return artifact


def import_all_project_artifacts(
    repo_root: Path,
    dry_run: bool = False,
    artifact_type: str | None = None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "found": 0,
        "imported": 0,
        "updated": 0,
        "skipped": 0,
        "errors": [],
    }
    for path in iter_candidate_files(repo_root):
        try:
            current_type = classify_artifact(path, repo_root)
            if artifact_type and current_type != artifact_type:
                continue
            summary["found"] += 1
            metadata = compute_file_metadata(path, repo_root)
            if dry_run:
                exists = ProjectArtifact.objects.filter(file_path=metadata["file_path"]).exists()
                summary["updated" if exists else "imported"] += 1
                continue
            artifact = import_project_artifact(path, repo_root)
        except Exception as exc:  # pragma: no cover - surfaced by command/API summary.
            summary["skipped"] += 1
            summary["errors"].append({"path": str(path), "error": str(exc)})
            continue
        if not dry_run:
            if getattr(artifact, "_ingestion_was_created", False):
                summary["imported"] += 1
            else:
                summary["updated"] += 1
    return summary


def _walk_files(root: Path, repo_root: Path) -> Iterator[Path]:
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            children = sorted(current.iterdir(), key=lambda item: item.name)
        except OSError:
            continue
        for child in children:
            if child.is_dir():
                if child.name in EXCLUDED_DIRS or _is_outside_repo(child, repo_root):
                    continue
                stack.append(child)
                continue
            if child.is_file() and _is_candidate_file(child, repo_root):
                yield child


def _is_candidate_file(path: Path, repo_root: Path) -> bool:
    if _is_outside_repo(path, repo_root):
        return False
    if path.name.endswith(".pyc"):
        return False
    if _relative_path(path, repo_root) == Path("backend/db.sqlite3"):
        return False
    suffix = path.suffix.lower()
    if suffix in KNOWN_EXTENSIONS:
        return True
    try:
        size = path.stat().st_size
    except OSError:
        return False
    return size <= MAX_UNKNOWN_BINARY_SIZE and not _looks_binary(path)


def _is_outside_repo(path: Path, repo_root: Path) -> bool:
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return True
    return False


def _relative_path(path: Path, repo_root: Path) -> Path:
    return path.resolve().relative_to(Path(repo_root).resolve())


def _is_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    return not _looks_binary(path)


def _looks_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:2048]
    except OSError:
        return True
    return b"\0" in chunk


def _count_lines(path: Path) -> int | None:
    try:
        with path.open("rb") as file:
            return sum(chunk.count(b"\n") for chunk in iter(lambda: file.read(1024 * 1024), b""))
    except OSError:
        return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inspect_file(path: Path, suffix: str, line_count: int | None) -> dict[str, Any]:
    if suffix == ".json":
        return _inspect_json(path)
    if suffix == ".jsonl":
        return _inspect_jsonl(path, line_count)
    if suffix == ".csv":
        return _inspect_csv(path, line_count)
    if suffix in {".md", ".markdown"}:
        return _inspect_markdown(path)
    if suffix in {".yaml", ".yml"}:
        return _inspect_yaml(path)
    if suffix == ".png":
        return _inspect_png(path)
    return {}


def _inspect_json(path: Path) -> dict[str, Any]:
    if _too_large_to_parse(path):
        return {"json_preview": "skipped_large_file"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    if isinstance(data, dict):
        return {"top_level_keys": list(data.keys())[:100]}
    if isinstance(data, list):
        sample = data[0] if data else None
        return {
            "json_type": "list",
            "items_count": len(data),
            "sample_keys": list(sample.keys())[:100] if isinstance(sample, dict) else [],
        }
    return {"json_type": type(data).__name__}


def _inspect_jsonl(path: Path, line_count: int | None) -> dict[str, Any]:
    metadata: dict[str, Any] = {"estimated_row_count": line_count or 0}
    try:
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                first = json.loads(line)
                if isinstance(first, dict):
                    metadata["sample_keys"] = list(first.keys())[:100]
                break
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return metadata
    return metadata


def _inspect_csv(path: Path, line_count: int | None) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.reader(file)
            columns = next(reader, [])
    except (OSError, UnicodeDecodeError, csv.Error):
        columns = []
    return {
        "columns": columns[:100],
        "row_count": max((line_count or 0) - 1, 0),
    }


def _inspect_markdown(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as file:
            for _ in range(200):
                line = file.readline()
                if not line:
                    break
                stripped = line.strip()
                if stripped.startswith("#"):
                    return {"first_heading": stripped.lstrip("#").strip()}
    except OSError:
        return {}
    return {}


def _inspect_yaml(path: Path) -> dict[str, Any]:
    if _too_large_to_parse(path):
        return {"yaml_preview": "skipped_large_file"}
    try:
        import yaml  # type: ignore
    except ImportError:
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {"top_level_keys": list(data.keys())[:100]} if isinstance(data, dict) else {}


def _inspect_png(path: Path) -> dict[str, Any]:
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        return {}
    try:
        with Image.open(path) as image:
            return {"width": image.width, "height": image.height}
    except Exception:
        return {}


def _too_large_to_parse(path: Path) -> bool:
    try:
        return path.stat().st_size > MAX_PARSE_BYTES
    except OSError:
        return True


def _related_objects(relative_path: str, repo_root: Path) -> dict[str, Any]:
    return {
        "related_run": _related_run(relative_path, repo_root),
        "related_dataset": _related_dataset(relative_path, repo_root),
        "related_defense_profile": _related_defense_profile(relative_path, repo_root),
    }


def _related_run(relative_path: str, repo_root: Path) -> BenchmarkRun | None:
    artifact_run = BenchmarkRun.objects.filter(artifacts__file_path=relative_path).first()
    if artifact_run:
        return artifact_run
    for run in BenchmarkRun.objects.exclude(output_dir=""):
        output_dir = _normalize_db_path(run.output_dir, repo_root)
        if output_dir and (relative_path == output_dir or relative_path.startswith(f"{output_dir}/")):
            return run
    return None


def _related_dataset(relative_path: str, repo_root: Path) -> Dataset | None:
    for dataset in Dataset.objects.exclude(file_path=""):
        if _normalize_db_path(dataset.file_path, repo_root) == relative_path:
            return dataset
    return None


def _related_defense_profile(relative_path: str, repo_root: Path) -> DefenseProfile | None:
    for profile in DefenseProfile.objects.exclude(yaml_path=""):
        if _normalize_db_path(profile.yaml_path, repo_root) == relative_path:
            return profile
    return None


def _normalize_db_path(value: str, repo_root: Path) -> str:
    path = Path(value)
    try:
        if path.is_absolute():
            return str(path.resolve().relative_to(Path(repo_root).resolve()))
    except ValueError:
        return str(path)
    return str(path)
