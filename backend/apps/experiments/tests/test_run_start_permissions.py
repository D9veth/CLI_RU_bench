import pytest
from rest_framework.test import APIClient

from apps.configs_app.models import DefenseProfile, ModelEndpoint
from apps.datasets.models import Dataset
from apps.experiments.models import BenchmarkRun


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def create_run(status=BenchmarkRun.Status.PENDING):
    dataset = Dataset.objects.create(
        name="Pilot",
        slug=f"pilot-{status}",
        file_path="data/pilot.jsonl",
        dataset_type=Dataset.DatasetType.PILOT,
    )
    profile = DefenseProfile.objects.create(
        name=f"D0 {status}",
        slug=f"d0-{status}",
        level=DefenseProfile.Level.D0,
    )
    endpoint = ModelEndpoint.objects.create(
        name=f"Endpoint {status}",
        slug=f"endpoint-{status}",
        provider=ModelEndpoint.Provider.LMSTUDIO,
        model_name="local-model",
        base_url="http://localhost:1234/v1",
    )
    return BenchmarkRun.objects.create(
        title=f"Run {status}",
        model_endpoint=endpoint,
        dataset=dataset,
        defense_profile=profile,
        status=status,
    )


@pytest.mark.django_db
def test_viewer_cannot_start_run(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    run = create_run()

    response = client_for(user).post(f"/api/runs/{run.id}/start/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_researcher_can_start_pending_run(django_user_model, monkeypatch):
    user = django_user_model.objects.create_user(
        username="researcher",
        password="test-password",
        role=django_user_model.Role.RESEARCHER,
    )
    run = create_run()
    started = []
    monkeypatch.setattr("apps.experiments.views.start_run_async", lambda run_id: started.append(run_id))

    response = client_for(user).post(f"/api/runs/{run.id}/start/")

    assert response.status_code == 200
    assert started == [run.id]


@pytest.mark.django_db
def test_cannot_start_completed_run(django_user_model, monkeypatch):
    user = django_user_model.objects.create_user(
        username="researcher",
        password="test-password",
        role=django_user_model.Role.RESEARCHER,
    )
    run = create_run(status=BenchmarkRun.Status.COMPLETED)
    monkeypatch.setattr("apps.experiments.views.start_run_async", lambda run_id: None)

    response = client_for(user).post(f"/api/runs/{run.id}/start/")

    assert response.status_code == 400
