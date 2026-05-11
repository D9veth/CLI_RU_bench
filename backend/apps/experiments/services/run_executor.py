import json
import subprocess
import threading
import traceback
from pathlib import Path

from django.db import close_old_connections
from django.utils import timezone

from apps.artifacts.models import RunArtifact
from apps.experiments.models import BenchmarkRun
from apps.experiments.services.artifact_ingestion import (
    get_repo_root,
    import_artifacts_for_existing_run,
)


CLI_COMMAND = "bench"


def get_run_output_dir(run: BenchmarkRun) -> Path:
    return get_repo_root() / "runs_web" / run.run_id


def build_cli_command(run: BenchmarkRun) -> list[str]:
    output_dir = get_run_output_dir(run)
    output_dir.mkdir(parents=True, exist_ok=True)
    config_path = _write_generated_config(run, output_dir)
    dataset_path = _resolve_repo_path(run.dataset.file_path)

    command = [
        CLI_COMMAND,
        "run",
        "--config",
        str(config_path),
        "--dataset",
        str(dataset_path),
        "--out",
        str(output_dir.parent),
        "--resume",
        str(output_dir),
        "--resume-force",
    ]
    if run.model_endpoint.base_url:
        command.extend(["--base-url", run.model_endpoint.base_url])
    if run.model_endpoint.model_name:
        command.extend(["--model", run.model_endpoint.model_name])
    return command


def execute_run(run_id: int) -> None:
    close_old_connections()
    run = BenchmarkRun.objects.select_related(
        "model_endpoint",
        "dataset",
        "defense_profile",
    ).get(pk=run_id)
    if run.status != BenchmarkRun.Status.PENDING:
        return

    output_dir = get_run_output_dir(run)
    output_dir.mkdir(parents=True, exist_ok=True)
    run.status = BenchmarkRun.Status.RUNNING
    run.started_at = timezone.now()
    run.output_dir = _relative_output_dir(output_dir)
    run.save(update_fields=["status", "started_at", "output_dir", "updated_at"])

    stdout_path = output_dir / "stdout.log"
    stderr_path = output_dir / "stderr.log"

    try:
        command = build_cli_command(run)
        completed = subprocess.run(
            command,
            cwd=get_repo_root(),
            capture_output=True,
            text=True,
            check=False,
        )
        stdout_path.write_text(completed.stdout or "", encoding="utf-8")
        stderr_path.write_text(completed.stderr or "", encoding="utf-8")
        _register_log_artifacts(run, stdout_path, stderr_path)

        if completed.returncode == 0:
            import_artifacts_for_existing_run(run, output_dir)
            run.refresh_from_db()
            run.status = BenchmarkRun.Status.COMPLETED
            run.finished_at = run.finished_at or timezone.now()
            run.error_message = ""
            run.save(update_fields=["status", "finished_at", "error_message", "updated_at"])
            return

        run.status = BenchmarkRun.Status.FAILED
        run.finished_at = timezone.now()
        run.error_message = _error_message_for_returncode(completed)
        run.save(update_fields=["status", "finished_at", "error_message", "updated_at"])
    except Exception as exc:
        stdout_path.touch(exist_ok=True)
        stderr_path.write_text(traceback.format_exc(), encoding="utf-8")
        _register_log_artifacts(run, stdout_path, stderr_path)
        run.status = BenchmarkRun.Status.FAILED
        run.finished_at = timezone.now()
        run.error_message = str(exc)[:1000]
        run.save(update_fields=["status", "finished_at", "error_message", "updated_at"])
    finally:
        close_old_connections()


def start_run_async(run_id: int) -> None:
    thread = threading.Thread(target=execute_run, args=(run_id,), daemon=True)
    thread.start()


def _write_generated_config(run: BenchmarkRun, output_dir: Path) -> Path:
    config = _build_generated_config(run)
    config_path = output_dir / "web_run_config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return config_path


def _build_generated_config(run: BenchmarkRun) -> dict:
    extra = run.extra_params_json or {}
    target = {
        "provider": "openai_compatible",
        "base_url": run.model_endpoint.base_url,
        "model": run.model_endpoint.model_name,
        "api_key_env": extra.get("api_key_env", "OPENAI_API_KEY"),
        "timeout_sec": int(extra.get("timeout_sec", 60)),
        "retries": int(extra.get("retries", 2)),
        "max_concurrency": int(extra.get("max_concurrency", 1)),
    }
    target.update(extra.get("target", {}))

    generation = {
        "temperature": (
            run.temperature_override
            if run.temperature_override is not None
            else run.model_endpoint.default_temperature
        ),
        "top_p": extra.get("top_p", 0.95),
        "max_tokens": (
            run.max_tokens_override
            if run.max_tokens_override is not None
            else run.model_endpoint.default_max_tokens
        ),
    }
    generation.update(extra.get("generation", {}))

    profile = (
        run.defense_profile.level
        if run.defense_profile.level != "custom"
        else run.defense_profile.name
    )
    defense = {"profile": profile}
    defense.update(run.defense_profile.parameters_json or {})
    defense.update(extra.get("defense", {}))

    run_section = {"repeats": int(extra.get("repeats", 1))}
    run_section.update(extra.get("run", {}))

    return {
        "target": target,
        "generation": generation,
        "defense": defense,
        "run": run_section,
    }


def _resolve_repo_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return get_repo_root() / candidate


def _relative_output_dir(output_dir: Path) -> str:
    try:
        return str(output_dir.resolve().relative_to(get_repo_root().resolve()))
    except ValueError:
        return str(output_dir)


def _register_log_artifacts(run: BenchmarkRun, stdout_path: Path, stderr_path: Path) -> None:
    for path in (stdout_path, stderr_path):
        RunArtifact.objects.update_or_create(
            run=run,
            file_path=_relative_output_dir(path),
            defaults={
                "artifact_type": RunArtifact.ArtifactType.LOG,
                "size_bytes": path.stat().st_size if path.exists() else 0,
            },
        )


def _error_message_for_returncode(completed: subprocess.CompletedProcess) -> str:
    stderr = (completed.stderr or "").strip()
    stdout = (completed.stdout or "").strip()
    message = stderr or stdout or f"CLI process exited with code {completed.returncode}"
    return message[:1000]
