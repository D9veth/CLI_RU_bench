import pytest
from rest_framework.test import APIClient

from apps.configs_app.models import DefenseProfile, ModelEndpoint
from apps.datasets.models import Dataset
from apps.experiments.models import BenchmarkRun, RunMetrics


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def create_dependencies():
    dataset = Dataset.objects.create(
        name="Merged safety utility",
        slug="merged-safety-utility",
        file_path="data/merged_safety_utility.jsonl",
        dataset_type=Dataset.DatasetType.FULL,
    )
    profile = DefenseProfile.objects.create(
        name="D2",
        slug="d2",
        level=DefenseProfile.Level.D2,
    )
    model_a = ModelEndpoint.objects.create(
        name="Gemma 3 12B",
        slug="gemma-3-12b",
        provider=ModelEndpoint.Provider.OPENAI_COMPATIBLE,
        model_name="gemma-3-12b",
        base_url="http://localhost:1234/v1",
    )
    model_b = ModelEndpoint.objects.create(
        name="Qwen2.5 7B",
        slug="qwen-25-7b",
        provider=ModelEndpoint.Provider.OPENAI_COMPATIBLE,
        model_name="qwen2.5-7b",
        base_url="http://localhost:1235/v1",
    )
    return dataset, profile, model_a, model_b


def create_run(title, model, dataset, profile):
    run = BenchmarkRun.objects.create(
        title=title,
        model_endpoint=model,
        dataset=dataset,
        defense_profile=profile,
        status=BenchmarkRun.Status.COMPLETED,
    )
    RunMetrics.objects.create(
        run=run,
        proxy_asr=0.2,
        one_minus_asr=0.8,
        fpr=0.04,
        u_mean=0.7,
        p95_latency=1200,
        total_cases=20,
    )
    return run


@pytest.mark.django_db
def test_viewer_can_compare_runs(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    dataset, profile, model_a, model_b = create_dependencies()
    run_a = create_run("Run A", model_a, dataset, profile)
    run_b = create_run("Run B", model_b, dataset, profile)

    response = client_for(user).get(f"/api/compare/runs/?run_a={run_a.id}&run_b={run_b.id}")

    assert response.status_code == 200
    assert response.data["run_a"]["id"] == run_a.id
    assert response.data["run_b"]["id"] == run_b.id
    assert response.data["metrics"][0]["key"] == "proxy_asr"
    assert response.data["metrics"][0]["label"] == "proxy-ASR"


@pytest.mark.django_db
def test_unauthenticated_user_cannot_compare_runs():
    response = APIClient().get("/api/compare/runs/?run_a=1&run_b=2")

    assert response.status_code == 401


@pytest.mark.django_db
def test_compare_runs_returns_400_for_missing_params(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )

    response = client_for(user).get("/api/compare/runs/")

    assert response.status_code == 400


@pytest.mark.django_db
def test_compare_runs_returns_404_for_unknown_run(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    dataset, profile, model_a, _model_b = create_dependencies()
    run_a = create_run("Run A", model_a, dataset, profile)

    response = client_for(user).get(f"/api/compare/runs/?run_a={run_a.id}&run_b=999")

    assert response.status_code == 404


@pytest.mark.django_db
def test_compare_runs_returns_400_when_metrics_missing(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    dataset, profile, model_a, model_b = create_dependencies()
    run_a = create_run("Run A", model_a, dataset, profile)
    run_b = BenchmarkRun.objects.create(
        title="Run B",
        model_endpoint=model_b,
        dataset=dataset,
        defense_profile=profile,
        status=BenchmarkRun.Status.COMPLETED,
    )

    response = client_for(user).get(f"/api/compare/runs/?run_a={run_a.id}&run_b={run_b.id}")

    assert response.status_code == 400
    assert "метрик" in response.data["detail"]


@pytest.mark.django_db
def test_compare_runs_export_returns_csv(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    dataset, profile, model_a, model_b = create_dependencies()
    run_a = create_run("Run A", model_a, dataset, profile)
    run_b = create_run("Run B", model_b, dataset, profile)

    response = client_for(user).get(f"/api/compare/runs/export.csv?run_a={run_a.id}&run_b={run_b.id}")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    assert b"metric,value_a,value_b,delta,better,direction" in response.content
