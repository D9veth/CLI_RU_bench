from __future__ import annotations

import json
from pathlib import Path
import typer

from bench.core.config import RunConfig
from bench.core.dataset import load_dataset
from bench.core.model.factory import build_client
from bench.core.preflight import run_preflight
from bench.core.runner import run_benchmark
from bench.core.storage import create_run_dir, write_preflight, write_run_config, write_summary, write_report

app = typer.Typer(add_completion=False, help="LLM defense benchmark CLI (MVP).")

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
    repeats: int = typer.Option(None, "--repeats", "-r", min=1, help="Overrides repeats in config."),
    out_dir: Path = typer.Option(Path("runs"), "--out", "-o", help="Output directory for run artifacts."),
    skip_preflight: bool = typer.Option(False, "--skip-preflight", help="Skip connectivity check (not recommended)."),
    base_url: str = typer.Option(None, "--base-url", help="Override target.base_url"),
    endpoint_url: str = typer.Option(None, "--endpoint-url", help="Override target.endpoint_url"),
    model: str = typer.Option(None, "--model", help="Override target.model"),
    api_key_env: str = typer.Option(None, "--api-key-env", help="Override target.api_key_env"),
):
    """Run benchmark and write artifacts."""
    run_cfg = RunConfig.load(config)
    if base_url: run_cfg.target.base_url = base_url
    if endpoint_url: run_cfg.target.endpoint_url = endpoint_url
    if model: run_cfg.target.model = model
    if api_key_env: run_cfg.target.api_key_env = api_key_env
    if repeats is not None:
        run_cfg.run.repeats = repeats

    cases = load_dataset(dataset)
    run_dir, run_id = create_run_dir(out_dir)

    write_run_config(run_dir, run_cfg, dataset_path=str(dataset))
    client = build_client(run_cfg.target)

    if not skip_preflight:
        preflight = run_preflight(client, run_cfg)
        write_preflight(run_dir, preflight)
        if not preflight.ok:
            typer.secho("Preflight failed; aborting run.", fg=typer.colors.RED)
            raise typer.Exit(code=2)

    results, summary = run_benchmark(client=client, run_cfg=run_cfg, cases=cases, run_dir=run_dir)
    write_summary(run_dir, summary)
    write_report(run_dir, summary)
    typer.secho(f"Done. run_id={run_id}  artifacts={run_dir}", fg=typer.colors.GREEN)

if __name__ == "__main__":
    app()
