import json

import pytest
from rest_framework.test import APIClient

from apps.experiments.models import BenchmarkRun


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def create_mock_run(root):
    run_dir = root / "runs" / "api_ingest_run"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(
        json.dumps({"proxy_asr": 0.3, "total_cases": 1}),
        encoding="utf-8",
    )
    (run_dir / "run_config.json").write_text(
        json.dumps(
            {
                "run_id": "api_ingest_run",
                "target": {
                    "base_url": "http://localhost:1234/v1",
                    "model": "local-model",
                },
                "dataset_path": "data/pilot_20.jsonl",
                "defense": {"profile": "D2"},
            }
        ),
        encoding="utf-8",
    )


@pytest.mark.django_db
def test_runs_ingest_endpoint_imports_runs(tmp_path, django_user_model, monkeypatch):
    user = django_user_model.objects.create_user(
        username="researcher",
        password="test-password",
        role=django_user_model.Role.RESEARCHER,
    )
    create_mock_run(tmp_path)
    monkeypatch.setattr("apps.experiments.views.get_repo_root", lambda: tmp_path)

    response = client_for(user).post("/api/runs/ingest/")

    assert response.status_code == 200
    assert response.data["found"] == 1
    assert response.data["imported"] == 1
    assert BenchmarkRun.objects.filter(run_id="api_ingest_run").exists()
