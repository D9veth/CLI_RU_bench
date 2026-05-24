import pytest

from apps.configs_app.models import DefenseProfile, ModelEndpoint
from apps.datasets.models import Dataset
from apps.experiments.models import BenchmarkRun, RunMetrics
from apps.experiments.services.model_comparison import compare_runs


def create_dependencies(suffix=""):
    dataset = Dataset.objects.create(
        name=f"Dataset {suffix or 'main'}",
        slug=f"dataset-{suffix or 'main'}",
        file_path=f"data/{suffix or 'main'}.jsonl",
        dataset_type=Dataset.DatasetType.PILOT,
    )
    defense_profile = DefenseProfile.objects.create(
        name=f"D2 {suffix or 'main'}",
        slug=f"d2-{suffix or 'main'}",
        level=DefenseProfile.Level.D2,
    )
    model_a = ModelEndpoint.objects.create(
        name=f"Model A {suffix or 'main'}",
        slug=f"model-a-{suffix or 'main'}",
        provider=ModelEndpoint.Provider.OPENAI_COMPATIBLE,
        model_name="model-a",
        base_url="http://localhost:1234/v1",
    )
    model_b = ModelEndpoint.objects.create(
        name=f"Model B {suffix or 'main'}",
        slug=f"model-b-{suffix or 'main'}",
        provider=ModelEndpoint.Provider.OPENAI_COMPATIBLE,
        model_name="model-b",
        base_url="http://localhost:1235/v1",
    )
    return dataset, defense_profile, model_a, model_b


def create_run(title, model, dataset, profile):
    return BenchmarkRun.objects.create(
        title=title,
        model_endpoint=model,
        dataset=dataset,
        defense_profile=profile,
        status=BenchmarkRun.Status.COMPLETED,
    )


@pytest.mark.django_db
def test_compare_runs_calculates_delta_and_winners():
    dataset, profile, model_a, model_b = create_dependencies()
    run_a = create_run("Run A", model_a, dataset, profile)
    run_b = create_run("Run B", model_b, dataset, profile)
    RunMetrics.objects.create(
        run=run_a,
        proxy_asr=0.15,
        one_minus_asr=0.85,
        fpr=0.05,
        u_mean=0.72,
        total_cases=100,
    )
    RunMetrics.objects.create(
        run=run_b,
        proxy_asr=0.35,
        one_minus_asr=0.65,
        fpr=0.03,
        u_mean=0.61,
        total_cases=100,
    )

    result = compare_runs(run_a, run_b)
    metrics = {metric["key"]: metric for metric in result["metrics"]}

    assert metrics["proxy_asr"]["delta"] == pytest.approx(-0.20)
    assert metrics["proxy_asr"]["better"] == "a"
    assert metrics["u_mean"]["delta"] == pytest.approx(0.11)
    assert metrics["u_mean"]["better"] == "a"
    assert metrics["fpr"]["better"] == "b"
    assert result["winner_by_metric"]["proxy_asr"] == "a"
    assert result["winner_by_metric"]["u_mean"] == "a"


@pytest.mark.django_db
def test_compare_runs_returns_warnings_for_mismatched_inputs():
    dataset_a, profile_a, model_a, model_b = create_dependencies("a")
    dataset_b = Dataset.objects.create(
        name="Dataset b",
        slug="dataset-b-extra",
        file_path="data/b.jsonl",
        dataset_type=Dataset.DatasetType.PILOT,
    )
    profile_b = DefenseProfile.objects.create(
        name="D3 b",
        slug="d3-b-extra",
        level=DefenseProfile.Level.D3,
    )
    run_a = create_run("Run A", model_a, dataset_a, profile_a)
    run_b = create_run("Run B", model_b, dataset_b, profile_b)
    RunMetrics.objects.create(run=run_a, proxy_asr=0.15, u_mean=0.72, total_cases=100)
    RunMetrics.objects.create(run=run_b, proxy_asr=0.35, u_mean=0.61, total_cases=90)

    result = compare_runs(run_a, run_b)
    warning_codes = {warning["code"] for warning in result["warnings"]}

    assert "different_dataset" in warning_codes
    assert "different_defense_profile" in warning_codes
    assert "different_total_cases" in warning_codes
