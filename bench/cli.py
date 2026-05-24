from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
import typer

from bench.core.config import RunConfig
from bench.core.dataset import load_dataset
from bench.core.dataset_validate import validate_dataset_file
from bench.core.manual_audit import create_audit_sample, score_annotations, validate_annotations
from bench.core.model.factory import build_client
from bench.core.preflight import run_preflight
from bench.core.runner import run_benchmark
from bench.core.storage import (
    build_run_metadata,
    create_run_dir,
    sha256_file,
    utc_now_iso,
    write_preflight,
    write_run_config,
    write_summary,
    write_report,
)

app = typer.Typer(add_completion=False, help="LLM defense benchmark CLI (MVP).")
audit_app = typer.Typer(help="Manual evaluator audit workflow.")
app.add_typer(audit_app, name="audit")


@audit_app.command("sample")
def audit_sample_cmd(
    cases_file: Optional[list[Path]] = typer.Option(
        None,
        "--cases-file",
        exists=True,
        readable=True,
        help="Case-level JSONL file. Can be passed multiple times.",
    ),
    runs_dir: Optional[Path] = typer.Option(
        None,
        "--runs-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Directory with benchmark run artifacts.",
    ),
    out: Path = typer.Option(..., "--out", help="Output directory for manual audit artifacts."),
    glob_pattern: str = typer.Option("**/cases.jsonl", "--glob", help="Glob used under --runs-dir."),
    n: int = typer.Option(250, "--n", min=1, help="Total sample size when per-bucket sizes are omitted."),
    attack_n: Optional[int] = typer.Option(None, "--attack-n", min=0, help="Number of attack samples."),
    benign_n: Optional[int] = typer.Option(None, "--benign-n", min=0, help="Number of benign samples."),
    borderline_n: Optional[int] = typer.Option(None, "--borderline-n", min=0, help="Number of borderline samples."),
    seed: int = typer.Option(42, "--seed", help="Deterministic sampling seed."),
    redact_secrets: bool = typer.Option(
        True,
        "--redact-secrets/--no-redact-secrets",
        help="Redact secret-like strings before writing annotation CSV.",
    ),
    max_output_chars: int = typer.Option(6000, "--max-output-chars", min=1, help="Output text truncation limit."),
    max_prompt_chars: int = typer.Option(4000, "--max-prompt-chars", min=1, help="Prompt text truncation limit."),
    include_utility: bool = typer.Option(
        False,
        "--include-utility/--exclude-utility",
        help="Include utility cases in addition to safety cases.",
    ),
    balanced_by: str = typer.Option(
        "category,defense_profile,model",
        "--balanced-by",
        help="Comma-separated fields used for best-effort stratification.",
    ),
    overwrite: bool = typer.Option(False, "--overwrite", help="Allow writing into a non-empty output directory."),
):
    """Create a blind CSV sample for manual evaluator annotation."""
    try:
        result = create_audit_sample(
            cases_files=cases_file,
            runs_dir=runs_dir,
            out_dir=out,
            glob_pattern=glob_pattern,
            n=n,
            attack_n=attack_n,
            benign_n=benign_n,
            borderline_n=borderline_n,
            seed=seed,
            redact_secrets=redact_secrets,
            max_output_chars=max_output_chars,
            max_prompt_chars=max_prompt_chars,
            include_utility=include_utility,
            balanced_by=balanced_by,
            overwrite=overwrite,
        )
    except Exception as exc:
        typer.secho(f"Audit sample failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=2)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@audit_app.command("validate")
def audit_validate_cmd(
    annotations: Path = typer.Option(..., "--annotations", exists=True, readable=True, help="Filled annotation CSV."),
    manifest: Path = typer.Option(..., "--manifest", exists=True, readable=True, help="audit_manifest.json."),
    allow_missing: bool = typer.Option(False, "--allow-missing", help="Treat missing labels as warnings."),
):
    """Validate a filled manual annotation CSV."""
    result = validate_annotations(
        annotations_path=annotations,
        manifest_path=manifest,
        allow_missing=allow_missing,
    )
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
    raise typer.Exit(code=0 if result["ok"] else 2)


@audit_app.command("score")
def audit_score_cmd(
    annotations: Path = typer.Option(..., "--annotations", exists=True, readable=True, help="Filled annotation CSV."),
    manifest: Path = typer.Option(..., "--manifest", exists=True, readable=True, help="audit_manifest.json."),
    out: Path = typer.Option(..., "--out", help="Output directory for scoring artifacts."),
    exclude_ambiguous: bool = typer.Option(
        True,
        "--exclude-ambiguous/--include-ambiguous",
        help="Exclude rows marked human_ambiguous=1.",
    ),
    bootstrap: int = typer.Option(0, "--bootstrap", min=0, help="Bootstrap iterations for 95% CI."),
    seed: int = typer.Option(42, "--seed", help="Deterministic bootstrap seed."),
    by: str = typer.Option("category,defense_profile,model", "--by", help="Comma-separated grouping fields."),
    min_group_size: int = typer.Option(10, "--min-group-size", min=1, help="Minimum rows for grouped metrics."),
    allow_missing: bool = typer.Option(False, "--allow-missing", help="Score partial annotations."),
    positive_label: Optional[str] = typer.Option(
        None,
        "--positive-label",
        help="Score only one task: attack_success|refusal|leakage|policy_violation|false_refusal.",
    ),
):
    """Compare evaluator labels with human labels and write metrics/confusion matrices."""
    try:
        result = score_annotations(
            annotations_path=annotations,
            manifest_path=manifest,
            out_dir=out,
            exclude_ambiguous=exclude_ambiguous,
            bootstrap=bootstrap,
            seed=seed,
            by=by,
            min_group_size=min_group_size,
            allow_missing=allow_missing,
            positive_label=positive_label,
        )
    except Exception as exc:
        typer.secho(f"Audit score failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=2)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("validate-dataset")
def validate_dataset_cmd(
    in_path: Path = typer.Option(..., "--in", exists=True, readable=True, help="Dataset YAML/JSONL path."),
    out: Path = typer.Option(
        Path("dataset_validation_report.json"),
        "--out",
        help="Where to write validation report JSON.",
    ),
):
    """Validate dataset schema/content and write dataset_validation_report.json."""
    report = validate_dataset_file(in_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    counts = report.counts
    typer.echo(
        f"Dataset validation: ok={report.ok}  items={counts.get('n_items', 0)}  "
        f"errors={counts.get('n_errors', 0)}  warnings={counts.get('n_warnings', 0)}"
    )
    typer.echo(f"Report written to: {out}")

    if report.errors:
        typer.secho("Errors:", fg=typer.colors.RED)
        for item in report.errors:
            idx = item.get("index")
            cid = item.get("case_id")
            field = item.get("field")
            prefix = f"[#{idx}]" if idx is not None else "[dataset]"
            if cid:
                prefix += f" id={cid}"
            if field:
                prefix += f" field={field}"
            typer.echo(f"  - {prefix}: {item.get('message')}")

    if report.warnings:
        typer.secho("Warnings:", fg=typer.colors.YELLOW)
        for item in report.warnings[:50]:
            idx = item.get("index")
            cid = item.get("case_id")
            field = item.get("field")
            prefix = f"[#{idx}]" if idx is not None else "[dataset]"
            if cid:
                prefix += f" id={cid}"
            if field:
                prefix += f" field={field}"
            typer.echo(f"  - {prefix}: {item.get('message')}")
        if len(report.warnings) > 50:
            typer.echo(f"  ... and {len(report.warnings) - 50} more warnings")

    raise typer.Exit(code=0 if report.ok else 2)

@app.command()
def doctor(
    config: Path = typer.Option(..., "--config", "-c", exists=True, readable=True, help="Run config YAML/JSON."),
):
    """Check connectivity and capabilities (preflight)."""
    run_cfg = RunConfig.load(config)
    client = build_client(run_cfg.target)
    preflight = run_preflight(client, run_cfg)
    typer.echo(json.dumps(preflight.model_dump(), ensure_ascii=False, indent=2))
    raise typer.Exit(code=0 if preflight.ok else 2)

@app.command()
def run(
    config: Path = typer.Option(..., "--config", "-c", exists=True, readable=True, help="Run config YAML/JSON."),
    dataset: Path = typer.Option(..., "--dataset", "-d", exists=True, readable=True, help="Dataset YAML/JSONL."),
    split: str = typer.Option("dev", "--split", help="Dataset split label to record in artifacts: dev|test"),
    dataset_id: str = typer.Option(None, "--dataset-id", help="Stable dataset identifier for reproducibility."),
    dataset_version: str = typer.Option(None, "--dataset-version", help="Dataset version/tag for reproducibility."),
    repeats: int = typer.Option(None, "--repeats", "-r", min=1, help="Overrides repeats in config."),
    out_dir: Path = typer.Option(Path("runs"), "--out", "-o", help="Output directory for run artifacts."),
    resume: Optional[Path] = typer.Option(
        None,
        "--resume",
        help="Resume an existing run directory (uses existing cases.jsonl and appends missing attempts).",
    ),
    resume_force: bool = typer.Option(
        False,
        "--resume-force",
        help="Allow resume even when dataset_hash/config_hash mismatch with existing run_config.json.",
    ),
    skip_preflight: bool = typer.Option(False, "--skip-preflight", help="Skip connectivity check (not recommended)."),
    base_url: str = typer.Option(None, "--base-url", help="Override target.base_url"),
    endpoint_url: str = typer.Option(None, "--endpoint-url", help="Override target.endpoint_url"),
    model: str = typer.Option(None, "--model", help="Override target.model"),
    api_key_env: str = typer.Option(None, "--api-key-env", help="Override target.api_key_env"),
):
    """Run benchmark and write artifacts."""
    split = (split or "dev").strip().lower()
    if split not in {"dev", "test"}:
        typer.secho("--split must be one of: dev, test", fg=typer.colors.RED)
        raise typer.Exit(code=2)

    run_cfg = RunConfig.load(config)
    if base_url: run_cfg.target.base_url = base_url
    if endpoint_url: run_cfg.target.endpoint_url = endpoint_url
    if model: run_cfg.target.model = model
    if api_key_env: run_cfg.target.api_key_env = api_key_env
    if repeats is not None:
        run_cfg.run.repeats = repeats

    cases = load_dataset(dataset)
    dataset_hash = sha256_file(dataset)
    existing_run_cfg = None

    if resume is not None:
        run_dir = Path(resume)
        if not run_dir.exists() or not run_dir.is_dir():
            typer.secho(f"--resume path is not a directory: {run_dir}", fg=typer.colors.RED)
            raise typer.Exit(code=2)
        run_id = run_dir.name
        existing_cfg_path = run_dir / "run_config.json"
        if existing_cfg_path.exists():
            try:
                existing_run_cfg = json.loads(existing_cfg_path.read_text(encoding="utf-8"))
            except Exception as e:
                typer.secho(f"Failed to read existing run_config.json: {e}", fg=typer.colors.RED)
                raise typer.Exit(code=2)

            expected_meta = build_run_metadata(
                run_cfg,
                dataset_path=str(dataset),
                dataset_split=split,
                dataset_hash=dataset_hash,
                dataset_id=dataset_id,
                dataset_version=dataset_version,
            )
            mismatches = []
            for key in ("dataset_hash", "config_hash"):
                old = existing_run_cfg.get(key)
                new = expected_meta.get(key)
                if old != new:
                    mismatches.append((key, old, new))

            if mismatches and not resume_force:
                typer.secho("Resume blocked: metadata mismatch in existing run_config.json", fg=typer.colors.RED)
                for key, old, new in mismatches:
                    typer.echo(f"  - {key}: existing={old!r} new={new!r}")
                typer.echo("Use --resume-force to continue anyway.")
                raise typer.Exit(code=2)
            if mismatches and resume_force:
                typer.secho("Resume forced despite metadata mismatch:", fg=typer.colors.YELLOW)
                for key, old, new in mismatches:
                    typer.echo(f"  - {key}: existing={old!r} new={new!r}")
    else:
        run_dir, run_id = create_run_dir(out_dir)

    started_at = (
        existing_run_cfg.get("started_at")
        if isinstance(existing_run_cfg, dict) and existing_run_cfg.get("started_at")
        else utc_now_iso()
    )
    dataset_id_effective = (
        dataset_id
        if dataset_id is not None
        else (existing_run_cfg.get("dataset_id") if isinstance(existing_run_cfg, dict) else None)
    )
    dataset_version_effective = (
        dataset_version
        if dataset_version is not None
        else (existing_run_cfg.get("dataset_version") if isinstance(existing_run_cfg, dict) else None)
    )
    run_config_kwargs = {
        "dataset_path": str(dataset),
        "dataset_split": split,
        "dataset_hash": dataset_hash,
        "dataset_id": dataset_id_effective,
        "dataset_version": dataset_version_effective,
        "started_at": started_at,
    }

    run_meta = write_run_config(run_dir, run_cfg, **run_config_kwargs)
    client = build_client(run_cfg.target)

    if not skip_preflight:
        preflight = run_preflight(client, run_cfg)
        write_preflight(run_dir, preflight)
        if not preflight.ok:
            run_meta = write_run_config(run_dir, run_cfg, finished_at=utc_now_iso(), **run_config_kwargs)
            typer.secho("Preflight failed; aborting run.", fg=typer.colors.RED)
            raise typer.Exit(code=2)

    results, summary = run_benchmark(client=client, run_cfg=run_cfg, cases=cases, run_dir=run_dir)
    run_meta = write_run_config(run_dir, run_cfg, finished_at=utc_now_iso(), **run_config_kwargs)
    write_summary(run_dir, summary, run_meta=run_meta)
    write_report(run_dir, summary)
    typer.secho(f"Done. run_id={run_id}  artifacts={run_dir}", fg=typer.colors.GREEN)

if __name__ == "__main__":
    app()
