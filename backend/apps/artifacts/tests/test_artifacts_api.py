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
        name="Baseline",
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
        title="Artifact run",
        model_endpoint=model_endpoint,
        dataset=dataset,
        defense_profile=defense_profile,
    )


@pytest.mark.django_db
def test_researcher_can_create_artifact_for_run(django_user_model):
    user = django_user_model.objects.create_user(
        username="researcher",
        password="test-password",
        role=django_user_model.Role.RESEARCHER,
    )
    run = create_run()
    payload = {
        "run": run.id,
        "artifact_type": RunArtifact.ArtifactType.SUMMARY,
        "file_path": "runs/demo/summary.json",
        "size_bytes": 512,
    }

    response = client_for(user).post("/api/artifacts/", payload, format="json")

    assert response.status_code == 201
    assert RunArtifact.objects.filter(run=run, artifact_type=RunArtifact.ArtifactType.SUMMARY).exists()


@pytest.mark.django_db
def test_run_artifacts_endpoint_returns_artifacts(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    run = create_run()
    RunArtifact.objects.create(
        run=run,
        artifact_type=RunArtifact.ArtifactType.REPORT,
        file_path="runs/demo/report.md",
        size_bytes=1024,
    )

    response = client_for(user).get(f"/api/runs/{run.id}/artifacts/")

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["artifact_type"] == RunArtifact.ArtifactType.REPORT
