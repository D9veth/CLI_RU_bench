import io
import json

import pytest
from django.core.management import call_command

from apps.experiments.models import BenchmarkRun


def create_mock_run(root):
    run_dir = root / "runs" / "command_run"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(
        json.dumps({"proxy_asr": 0.4, "total_cases": 1}),
        encoding="utf-8",
    )
    (run_dir / "run_config.json").write_text(
        json.dumps(
            {
                "run_id": "command_run",
                "target": {
                    "base_url": "http://localhost:1234/v1",
                    "model": "local-model",
                },
                "dataset_path": "data/sample.jsonl",
                "defense": {"profile": "D0"},
            }
        ),
        encoding="utf-8",
    )
    return run_dir


@pytest.mark.django_db
def test_ingest_runs_dry_run_does_not_import(tmp_path):
    create_mock_run(tmp_path)
    stdout = io.StringIO()

    call_command("ingest_runs", root=str(tmp_path), dry_run=True, stdout=stdout)

    assert "found=1 imported=0 updated=0 skipped=0" in stdout.getvalue()
    assert BenchmarkRun.objects.count() == 0


@pytest.mark.django_db
def test_ingest_runs_imports_mock_run(tmp_path):
    create_mock_run(tmp_path)
    stdout = io.StringIO()

    call_command("ingest_runs", root=str(tmp_path), stdout=stdout)

    assert "found=1 imported=1 updated=0 skipped=0" in stdout.getvalue()
    assert BenchmarkRun.objects.filter(run_id="command_run").exists()
