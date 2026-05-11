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


@pytest.mark.django_db
def test_logs_endpoint_returns_stdout_and_stderr(tmp_path, django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
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
    run = BenchmarkRun.objects.create(
        title="Log run",
        model_endpoint=endpoint,
        dataset=dataset,
        defense_profile=profile,
    )
    stdout_path = tmp_path / "stdout.log"
    stderr_path = tmp_path / "stderr.log"
    stdout_path.write_text("stdout content", encoding="utf-8")
    stderr_path.write_text("stderr content", encoding="utf-8")
    RunArtifact.objects.create(
        run=run,
        artifact_type=RunArtifact.ArtifactType.LOG,
        file_path=str(stdout_path),
    )
    RunArtifact.objects.create(
        run=run,
        artifact_type=RunArtifact.ArtifactType.LOG,
        file_path=str(stderr_path),
    )

    response = client_for(user).get(f"/api/runs/{run.id}/logs/")

    assert response.status_code == 200
    assert response.data == {"stdout": "stdout content", "stderr": "stderr content"}
