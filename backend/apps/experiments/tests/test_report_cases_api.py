import json

import pytest
from rest_framework.test import APIClient

from apps.artifacts.models import RunArtifact
from apps.configs_app.models import DefenseProfile, ModelEndpoint
from apps.datasets.models import Dataset
from apps.experiments.models import BenchmarkRun


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def create_run():
    dataset = Dataset.objects.create(
        name="Pilot 20",
        slug="pilot-20",
        file_path="data/pilot_20.jsonl",
        dataset_type=Dataset.DatasetType.PILOT,
    )
    defense_profile = DefenseProfile.objects.create(
        name="D0",
        slug="d0",
        level=DefenseProfile.Level.D0,
    )
    model_endpoint = ModelEndpoint.objects.create(
        name="Local LM Studio",
        slug="local-lm-studio",
        provider=ModelEndpoint.Provider.LMSTUDIO,
        model_name="local-model",
        base_url="http://localhost:1234/v1",
    )
    return BenchmarkRun.objects.create(
        run_id="artifact_endpoint_run",
        title="Artifact endpoint run",
        model_endpoint=model_endpoint,
        dataset=dataset,
        defense_profile=defense_profile,
        status=BenchmarkRun.Status.COMPLETED,
    )


@pytest.mark.django_db
def test_report_endpoint_returns_markdown(tmp_path, django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    run = create_run()
    report_path = tmp_path / "report.md"
    report_path.write_text("# Imported report\nBody\n", encoding="utf-8")
    RunArtifact.objects.create(
        run=run,
        artifact_type=RunArtifact.ArtifactType.REPORT,
        file_path=str(report_path),
    )

    response = client_for(user).get(f"/api/runs/{run.id}/report/")

    assert response.status_code == 200
    assert response.data["report"].startswith("# Imported report")


@pytest.mark.django_db
def test_cases_endpoint_returns_limited_cases(tmp_path, django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    run = create_run()
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text(
        "\n".join(json.dumps({"case_id": f"case_{idx}"}) for idx in range(3)),
        encoding="utf-8",
    )
    RunArtifact.objects.create(
        run=run,
        artifact_type=RunArtifact.ArtifactType.CASES,
        file_path=str(cases_path),
    )

    response = client_for(user).get(f"/api/runs/{run.id}/cases/?limit=2")

    assert response.status_code == 200
    assert response.data["limit"] == 2
    assert [case["case_id"] for case in response.data["cases"]] == ["case_0", "case_1"]
