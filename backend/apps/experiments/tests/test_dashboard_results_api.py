import pytest
from rest_framework.test import APIClient

from apps.configs_app.models import DefenseProfile, ModelEndpoint
from apps.datasets.models import Dataset
from apps.experiments.models import BenchmarkRun, RunMetrics


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def create_completed_run():
    dataset = Dataset.objects.create(
        name="Pilot 20",
        slug="pilot-20",
        file_path="data/pilot_20.jsonl",
        dataset_type=Dataset.DatasetType.PILOT,
    )
    defense_profile = DefenseProfile.objects.create(
        name="D1",
        slug="d1",
        level=DefenseProfile.Level.D1,
    )
    model_endpoint = ModelEndpoint.objects.create(
        name="Local LM Studio",
        slug="local-lm-studio",
        provider=ModelEndpoint.Provider.LMSTUDIO,
        model_name="local-model",
        base_url="http://localhost:1234/v1",
    )
    run = BenchmarkRun.objects.create(
        run_id="dashboard_run",
        title="Dashboard run",
        model_endpoint=model_endpoint,
        dataset=dataset,
        defense_profile=defense_profile,
        status=BenchmarkRun.Status.COMPLETED,
    )
    RunMetrics.objects.create(
        run=run,
        proxy_asr=0.2,
        one_minus_asr=0.8,
        fpr=0.05,
        u_mean=0.9,
        p95_latency=1000.0,
    )
    return run


@pytest.mark.django_db
def test_dashboard_returns_counts_and_avg_proxy_asr(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    create_completed_run()

    response = client_for(user).get("/api/dashboard/")

    assert response.status_code == 200
    assert response.data["total_runs"] == 1
    assert response.data["completed_runs"] == 1
    assert response.data["avg_proxy_asr"] == 0.2


@pytest.mark.django_db
def test_results_endpoints_return_run_data(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    create_completed_run()
    client = client_for(user)

    results = client.get("/api/results/")
    pareto = client.get("/api/results/pareto/")
    heatmap = client.get("/api/results/heatmap/")

    assert results.status_code == 200
    assert results.data[0]["run_id"] == "dashboard_run"
    assert results.data[0]["proxy_asr"] == 0.2
    assert pareto.status_code == 200
    assert pareto.data[0]["run_id"] == "dashboard_run"
    assert heatmap.status_code == 200
    assert heatmap.data["rows"] == ["local-model"]
    assert heatmap.data["columns"] == ["D1"]
    assert heatmap.data["values"] == [[0.2]]
