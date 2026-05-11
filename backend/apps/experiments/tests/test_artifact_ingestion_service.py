import json

import pytest

from apps.artifacts.models import RunArtifact
from apps.experiments.models import BenchmarkRun, RunMetrics
from apps.experiments.services.artifact_ingestion import find_run_dirs, import_run_dir


def create_mock_run(root):
    run_dir = root / "runs_matrix" / "20260511T120000Z_demo"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "safety": {
                    "asr": 0.25,
                    "tpr": 0.75,
                    "fpr": 0.1,
                    "latency_ms_p95": 1234.5,
                },
                "utility": {"u_mean": 0.88},
                "status_counts": {"ok": 2, "error": 1},
                "total_cases": 3,
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "run_config.json").write_text(
        json.dumps(
            {
                "run_id": "demo_run",
                "target": {
                    "provider": "openai_compatible",
                    "base_url": "http://localhost:1234/v1",
                    "model": "local-model",
                },
                "dataset_path": "data/pilot_20.jsonl",
                "defense": {"profile": "D1"},
                "config_source_path": "configs/defenses/d1.yaml",
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "report.md").write_text("# Demo report\n", encoding="utf-8")
    return run_dir


@pytest.mark.django_db
def test_find_run_dirs_and_import_run_dir_are_idempotent(tmp_path):
    run_dir = create_mock_run(tmp_path)

    assert find_run_dirs(tmp_path) == [run_dir]

    run = import_run_dir(run_dir)
    assert run.run_id == "demo_run"
    assert run.status == BenchmarkRun.Status.COMPLETED
    assert run.metrics.proxy_asr == 0.25
    assert run.metrics.one_minus_asr == 0.75
    assert run.metrics.u_mean == 0.88
    assert run.artifacts.filter(artifact_type=RunArtifact.ArtifactType.REPORT).exists()

    imported_again = import_run_dir(run_dir)

    assert imported_again.id == run.id
    assert BenchmarkRun.objects.count() == 1
    assert RunMetrics.objects.count() == 1
    assert RunArtifact.objects.count() == 3
