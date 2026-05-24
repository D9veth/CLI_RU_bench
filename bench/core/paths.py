from __future__ import annotations

from pathlib import Path


PROJECT_MARKERS = ("pyproject.toml", ".git", "README.md")


def find_repo_root(start: Path | None = None) -> Path:
    """Return the nearest project root using explicit repository markers."""
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if any((candidate / marker).exists() for marker in PROJECT_MARKERS):
            return candidate
    return current


def resolve_config_path(
    value: str | Path,
    *,
    config_dir: Path | None = None,
    repo_root: Path | None = None,
    label: str = "path",
    must_exist: bool = True,
) -> Path:
    """Resolve config paths as absolute, config-relative, then repo-root-relative."""
    raw_path = Path(value).expanduser()
    candidates: list[Path]
    if raw_path.is_absolute():
        candidates = [raw_path]
    else:
        base_dir = (config_dir or Path.cwd()).resolve()
        root = (repo_root or find_repo_root(base_dir)).resolve()
        candidates = [base_dir / raw_path, root / raw_path]

    for candidate in candidates:
        resolved = candidate.resolve()
        if not must_exist or resolved.exists():
            return resolved

    rendered = ", ".join(str(candidate.resolve()) for candidate in candidates)
    raise FileNotFoundError(f"Cannot resolve {label}: {value!r}. Tried: {rendered}")
