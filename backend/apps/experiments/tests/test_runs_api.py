import pytest
from rest_framework.test import APIClient

from apps.configs_app.models import DefenseProfile, ModelEndpoint
from apps.datasets.models import Dataset
from apps.experiments.models import BenchmarkRun


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def create_run_dependencies():
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
        yaml_path="configs/defenses/D0.yaml",
    )
    model_endpoint = ModelEndpoint.objects.create(
        name="Local LM Studio",
        slug="local-lm-studio",
        provider=ModelEndpoint.Provider.LMSTUDIO,
        model_name="local-model",
        base_url="http://localhost:1234/v1",
    )
    return dataset, defense_profile, model_endpoint


@pytest.mark.django_db
def test_researcher_can_create_run_with_auto_fields(django_user_model):
    user = django_user_model.objects.create_user(
        username="researcher",
        password="test-password",
        role=django_user_model.Role.RESEARCHER,
    )
    dataset, defense_profile, model_endpoint = create_run_dependencies()
    payload = {
        "title": "Demo run",
        "model_endpoint": model_endpoint.id,
        "dataset": dataset.id,
        "defense_profile": defense_profile.id,
    }

    response = client_for(user).post("/api/runs/", payload, format="json")

    assert response.status_code == 201
    assert response.data["created_by"] == user.id
    assert response.data["created_by_username"] == user.username
    assert response.data["status"] == BenchmarkRun.Status.PENDING
    assert response.data["run_id"].startswith("run_")
    assert response.data["config_snapshot_json"]["model_endpoint"]["name"] == model_endpoint.name


@pytest.mark.django_db
def test_viewer_cannot_create_run(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    dataset, defense_profile, model_endpoint = create_run_dependencies()
    payload = {
        "title": "Blocked run",
        "model_endpoint": model_endpoint.id,
        "dataset": dataset.id,
        "defense_profile": defense_profile.id,
    }

    response = client_for(user).post("/api/runs/", payload, format="json")

    assert response.status_code == 403


@pytest.mark.django_db
def test_viewer_can_read_run(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    dataset, defense_profile, model_endpoint = create_run_dependencies()
    run = BenchmarkRun.objects.create(
        title="Readable run",
        model_endpoint=model_endpoint,
        dataset=dataset,
        defense_profile=defense_profile,
    )

    response = client_for(user).get(f"/api/runs/{run.id}/")

    assert response.status_code == 200
    assert response.data["id"] == run.id
    assert response.data["run_id"].startswith("run_")
