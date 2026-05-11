import pytest
from rest_framework.test import APIClient

from apps.configs_app.models import DefenseProfile, ModelEndpoint
from apps.datasets.models import Dataset
from apps.experiments.models import BenchmarkRun, RunMetrics


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
        title="Metrics run",
        model_endpoint=model_endpoint,
        dataset=dataset,
        defense_profile=defense_profile,
    )


@pytest.mark.django_db
def test_researcher_can_create_metrics_for_run(django_user_model):
    user = django_user_model.objects.create_user(
        username="researcher",
        password="test-password",
        role=django_user_model.Role.RESEARCHER,
    )
    run = create_run()
    payload = {
        "run": run.id,
        "proxy_asr": 0.15,
        "one_minus_asr": 0.85,
        "total_cases": 20,
        "ok_cases": 19,
        "error_cases": 1,
    }

    response = client_for(user).post("/api/run-metrics/", payload, format="json")

    assert response.status_code == 201
    assert RunMetrics.objects.filter(run=run).exists()


@pytest.mark.django_db
def test_run_metrics_endpoint_returns_metrics(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    run = create_run()
    RunMetrics.objects.create(run=run, proxy_asr=0.2, total_cases=20)

    response = client_for(user).get(f"/api/runs/{run.id}/metrics/")

    assert response.status_code == 200
    assert response.data["run"] == run.id
    assert response.data["proxy_asr"] == 0.2
