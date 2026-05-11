import subprocess

import pytest

from apps.configs_app.models import DefenseProfile, ModelEndpoint
from apps.datasets.models import Dataset
from apps.experiments.models import BenchmarkRun
from apps.experiments.services.run_executor import execute_run


def create_run():
    dataset = Dataset.objects.create(
        name="Pilot",
        slug="pilot",
        file_path="data/pilot.jsonl",
        dataset_type=Dataset.DatasetType.PILOT,
    )
    profile = DefenseProfile.objects.create(name="D0", slug="d0", level=DefenseProfile.Level.D0)
    endpoint = ModelEndpoint.objects.create(
        name="Local LM Studio",
        slug="local-lm-studio",
        provider=ModelEndpoint.Provider.LMSTUDIO,
        model_name="local-model",
        base_url="http://localhost:1234/v1",
    )
    return BenchmarkRun.objects.create(
        run_id="failed_run",
        title="Failed run",
        model_endpoint=endpoint,
        dataset=dataset,
        defense_profile=profile,
        status=BenchmarkRun.Status.PENDING,
    )


@pytest.mark.django_db
def test_execute_run_failure_marks_failed_and_stores_error(tmp_path, monkeypatch):
    monkeypatch.setattr("apps.experiments.services.run_executor.get_repo_root", lambda: tmp_path)
    run = create_run()

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=1,
            stdout="bad stdout",
            stderr="benchmark failed",
        )

    monkeypatch.setattr("apps.experiments.services.run_executor.subprocess.run", fake_run)

    execute_run(run.id)

    run.refresh_from_db()
    assert run.status == BenchmarkRun.Status.FAILED
    assert "benchmark failed" in run.error_message
    assert (tmp_path / "runs_web" / "failed_run" / "stdout.log").read_text() == "bad stdout"
    assert (tmp_path / "runs_web" / "failed_run" / "stderr.log").read_text() == "benchmark failed"
