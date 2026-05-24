import csv

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsViewerOrAbove
from apps.experiments.models import BenchmarkRun
from apps.experiments.services.model_comparison import (
    MetricsMissingError,
    compare_runs,
    compare_runs_by_categories,
    top_different_cases,
)


class CompareRunsView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        run_a_id, run_b_id, error = _parse_run_ids(request)
        if error:
            return Response({"detail": error}, status=400)

        run_a = _get_run(run_a_id)
        run_b = _get_run(run_b_id)
        try:
            payload = compare_runs(run_a, run_b)
        except MetricsMissingError as exc:
            return Response({"detail": str(exc)}, status=400)

        payload["category_breakdown"] = compare_runs_by_categories(run_a, run_b)
        payload["top_different_cases"] = top_different_cases(run_a, run_b)
        return Response(payload)


class CompareRunsCsvView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        run_a_id, run_b_id, error = _parse_run_ids(request)
        if error:
            return Response({"detail": error}, status=400)

        run_a = _get_run(run_a_id)
        run_b = _get_run(run_b_id)
        try:
            payload = compare_runs(run_a, run_b)
        except MetricsMissingError as exc:
            return Response({"detail": str(exc)}, status=400)

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="compare_{run_a.id}_{run_b.id}.csv"'
        writer = csv.writer(response)
        writer.writerow(["metric", "value_a", "value_b", "delta", "better", "direction"])
        for metric in payload["metrics"]:
            writer.writerow(
                [
                    metric["key"],
                    _csv_value(metric["value_a"]),
                    _csv_value(metric["value_b"]),
                    _csv_value(metric["delta"]),
                    metric["better"] or "",
                    metric["direction"],
                ]
            )
        return response


class CompareOptionsView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        runs = (
            BenchmarkRun.objects.filter(status=BenchmarkRun.Status.COMPLETED)
            .select_related("model_endpoint", "dataset", "defense_profile", "metrics")
            .order_by("model_endpoint__name", "dataset__name", "defense_profile__name", "-finished_at", "-created_at")
        )
        options = [_option_run(run) for run in runs]
        return Response({"runs": options, "groups": _groups(options)})


def _parse_run_ids(request):
    raw_a = request.query_params.get("run_a")
    raw_b = request.query_params.get("run_b")
    if not raw_a or not raw_b:
        return None, None, "Query params run_a and run_b are required."
    try:
        run_a_id = int(raw_a)
        run_b_id = int(raw_b)
    except (TypeError, ValueError):
        return None, None, "Query params run_a and run_b must be integers."
    if run_a_id == run_b_id:
        return None, None, "Выберите два разных запуска."
    return run_a_id, run_b_id, None


def _get_run(run_id: int) -> BenchmarkRun:
    return get_object_or_404(
        BenchmarkRun.objects.select_related(
            "model_endpoint",
            "dataset",
            "defense_profile",
        ).select_related("metrics"),
        pk=run_id,
    )


def _csv_value(value):
    return "" if value is None else value


def _option_run(run: BenchmarkRun) -> dict:
    model = _model_name(run)
    return {
        "id": run.id,
        "run_id": run.run_id,
        "title": run.title,
        "model": model,
        "dataset": run.dataset.name,
        "dataset_id": run.dataset_id,
        "profile": run.defense_profile.name,
        "defense_profile_id": run.defense_profile_id,
        "status": run.status,
        "finished_at": run.finished_at,
        "label": f"{model} • {run.defense_profile.name} • {run.dataset.name} • {run.run_id}",
        "has_metrics": hasattr(run, "metrics"),
    }


def _model_name(run: BenchmarkRun) -> str:
    endpoint_name = run.model_endpoint.name or ""
    model_name = run.model_endpoint.model_name or ""
    normalized_name = endpoint_name.lower().replace("_", " ").replace("-", " ").strip()
    generic_local_names = {
        "local llm",
        "local lm studio",
        "local lmstudio",
        "unknown model endpoint",
    }
    if model_name and (not endpoint_name or normalized_name in generic_local_names):
        return model_name
    if endpoint_name and model_name and model_name.lower() not in endpoint_name.lower():
        return f"{endpoint_name} · {model_name}"
    return endpoint_name or model_name


def _groups(options: list[dict]) -> list[dict]:
    grouped = {}
    for option in options:
        key = (option["model"], option["dataset"], option["profile"])
        grouped.setdefault(
            key,
            {
                "model": option["model"],
                "dataset": option["dataset"],
                "profile": option["profile"],
                "runs": [],
            },
        )["runs"].append(option)
    return list(grouped.values())
