import json
from pathlib import Path

from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.audit import write_audit_log
from apps.accounts.permissions import IsResearcherOrAdmin, IsViewerOrAbove
from apps.artifacts.models import ProjectArtifact, RunArtifact
from apps.common.viewsets import RolePermissionViewSetMixin
from apps.configs_app.models import DefenseProfile, ModelEndpoint
from apps.datasets.models import Dataset
from apps.experiments.models import BenchmarkRun, RunMetrics
from apps.experiments.serializers import BenchmarkRunSerializer, RunMetricsSerializer
from apps.experiments.services.artifact_ingestion import get_repo_root, import_all_runs
from apps.experiments.services.run_executor import start_run_async


class BenchmarkRunViewSet(RolePermissionViewSetMixin, viewsets.ModelViewSet):
    read_actions = {"list", "retrieve", "logs", "progress"}
    write_actions = {"create", "update", "partial_update", "start", "cancel"}
    serializer_class = BenchmarkRunSerializer
    queryset = (
        BenchmarkRun.objects.select_related(
            "created_by",
            "model_endpoint",
            "dataset",
            "defense_profile",
        )
        .select_related("metrics")
        .all()
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        filters = {
            "status": self.request.query_params.get("status"),
            "model_endpoint_id": self.request.query_params.get("model_endpoint"),
            "dataset_id": self.request.query_params.get("dataset"),
            "defense_profile_id": self.request.query_params.get("defense_profile"),
            "created_by_id": self.request.query_params.get("created_by"),
        }
        for field_name, value in filters.items():
            if value not in (None, ""):
                queryset = queryset.filter(**{field_name: value})
        return queryset

    def perform_create(self, serializer):
        run = serializer.save(created_by=self.request.user, status=BenchmarkRun.Status.PENDING)
        if not run.output_dir:
            snapshot = run.config_snapshot_json or {}
            snapshot.setdefault("source", {})
            snapshot["source"]["output_dir"] = f"runs_web/{run.run_id}"
            run.output_dir = f"runs_web/{run.run_id}"
            run.config_snapshot_json = snapshot
            run.save(update_fields=["output_dir", "config_snapshot_json", "updated_at"])

    def destroy(self, request, *args, **kwargs):
        run = self.get_object()
        if run.status == BenchmarkRun.Status.COMPLETED:
            return super().destroy(request, *args, **kwargs)

        run.status = BenchmarkRun.Status.CANCELLED
        run.save(update_fields=["status", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        run = self.get_object()
        if run.status != BenchmarkRun.Status.PENDING:
            return Response(
                {"detail": "Only pending runs can be started."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        start_run_async(run.id)
        run.refresh_from_db()
        write_audit_log(request.user, action="start_run", object_type="BenchmarkRun", object_id=run.id)
        serializer = self.get_serializer(run)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        run = self.get_object()
        if run.status in {BenchmarkRun.Status.PENDING, BenchmarkRun.Status.QUEUED}:
            run.status = BenchmarkRun.Status.CANCELLED
            run.save(update_fields=["status", "updated_at"])
            write_audit_log(request.user, action="cancel_run", object_type="BenchmarkRun", object_id=run.id)
            return Response(self.get_serializer(run).data)
        if run.status == BenchmarkRun.Status.RUNNING:
            return Response(
                {"detail": "Cancel for running process is not implemented in MVP."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        return Response(
            {"detail": "Only pending or running runs can be cancelled."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["get"])
    def progress(self, request, pk=None):
        run = self.get_object()
        return Response(_read_progress(run))

    @action(detail=True, methods=["get"])
    def logs(self, request, pk=None):
        run = self.get_object()
        stdout_artifact = _log_artifact(run, "stdout.log")
        stderr_artifact = _log_artifact(run, "stderr.log")
        return Response(
            {
                "stdout": _read_artifact_text(stdout_artifact) if stdout_artifact else "",
                "stderr": _read_artifact_text(stderr_artifact) if stderr_artifact else "",
            }
        )


class RunMetricsViewSet(RolePermissionViewSetMixin, viewsets.ModelViewSet):
    serializer_class = RunMetricsSerializer
    queryset = RunMetrics.objects.select_related("run").all()


class RunMetricsByRunView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request, pk):
        run = get_object_or_404(BenchmarkRun, pk=pk)
        metrics = get_object_or_404(RunMetrics, run=run)
        serializer = RunMetricsSerializer(metrics)
        return Response(serializer.data)


class RunIngestView(APIView):
    permission_classes = [IsResearcherOrAdmin]

    def post(self, request):
        summary = import_all_runs(get_repo_root(), created_by=request.user)
        return Response(summary)


class DashboardView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        runs = BenchmarkRun.objects.select_related(
            "created_by",
            "model_endpoint",
            "dataset",
            "defense_profile",
        )
        completed_runs = runs.filter(status=BenchmarkRun.Status.COMPLETED)
        aggregates = completed_runs.aggregate(
            avg_proxy_asr=Avg("metrics__proxy_asr"),
            avg_one_minus_asr=Avg("metrics__one_minus_asr"),
            avg_fpr=Avg("metrics__fpr"),
            avg_u_mean=Avg("metrics__u_mean"),
            avg_p95_latency=Avg("metrics__p95_latency"),
        )
        latest_runs = BenchmarkRunSerializer(runs.order_by("-created_at")[:5], many=True).data
        dataset_distribution = {
            row["dataset__name"]: row["count"]
            for row in runs.values("dataset__name").annotate(count=Count("id")).order_by("dataset__name")
        }

        return Response(
            {
                "total_runs": runs.count(),
                "completed_runs": completed_runs.count(),
                "failed_runs": runs.filter(status=BenchmarkRun.Status.FAILED).count(),
                "pending_runs": runs.filter(status=BenchmarkRun.Status.PENDING).count(),
                "running_runs": runs.filter(status=BenchmarkRun.Status.RUNNING).count(),
                "models_count": ModelEndpoint.objects.count(),
                "datasets_count": Dataset.objects.count(),
                "defense_profiles_count": DefenseProfile.objects.count(),
                "project_artifacts_count": ProjectArtifact.objects.count(),
                "figures_count": ProjectArtifact.objects.filter(artifact_type=ProjectArtifact.ArtifactType.FIGURE).count(),
                "tables_count": ProjectArtifact.objects.filter(artifact_type=ProjectArtifact.ArtifactType.TABLE).count(),
                "reports_count": ProjectArtifact.objects.filter(
                    artifact_type__in=[
                        ProjectArtifact.ArtifactType.REPORT,
                        ProjectArtifact.ArtifactType.MARKDOWN,
                    ]
                ).count(),
                "datasets_files_count": ProjectArtifact.objects.filter(artifact_type=ProjectArtifact.ArtifactType.DATASET).count(),
                "configs_files_count": ProjectArtifact.objects.filter(artifact_type=ProjectArtifact.ArtifactType.CONFIG).count(),
                **aggregates,
                "latest_runs": latest_runs,
                "dataset_distribution": dataset_distribution,
                "asr_by_profile": _asr_by_profile(completed_runs),
                "heatmap_by_model_profile": _heatmap_rows(completed_runs),
            }
        )


class ResultsView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        runs = _completed_runs_with_metrics()
        return Response([_result_row(run) for run in runs])


class ParetoResultsView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        return Response(
            [
                {
                    "run_id": run.run_id,
                    "model": _model_display_name(run.model_endpoint),
                    "profile": run.defense_profile.name,
                    "defense_level": run.defense_profile.level,
                    "proxy_asr": run.metrics.proxy_asr,
                    "one_minus_asr": run.metrics.one_minus_asr,
                    "fpr": run.metrics.fpr,
                    "u_mean": run.metrics.u_mean,
                    "p95_latency": run.metrics.p95_latency,
                }
                for run in _completed_runs_with_metrics()
            ]
        )


class HeatmapResultsView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        grouped_rows = _heatmap_rows(_completed_runs_with_metrics())
        rows = sorted({row["model"] for row in grouped_rows})
        columns = sorted({row["profile"] for row in grouped_rows})
        lookup = {
            (row["model"], row["profile"]): row["proxy_asr"]
            for row in grouped_rows
        }
        values = [[lookup.get((row, column)) for column in columns] for row in rows]
        return Response({"rows": rows, "columns": columns, "values": values})


class RunReportView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request, pk):
        run = get_object_or_404(BenchmarkRun, pk=pk)
        artifact = (
            RunArtifact.objects.filter(run=run, artifact_type=RunArtifact.ArtifactType.REPORT)
            .order_by("id")
            .first()
        )
        report = _read_artifact_text(artifact) if artifact else ""
        return Response({"run": run.id, "run_id": run.run_id, "report": report})


class RunCasesView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request, pk):
        run = get_object_or_404(BenchmarkRun, pk=pk)
        limit = _parse_limit(request.query_params.get("limit"))
        offset = _parse_offset(request.query_params.get("offset"))
        status_filter = request.query_params.get("status")
        category_filter = request.query_params.get("category")
        artifact = (
            RunArtifact.objects.filter(run=run, artifact_type=RunArtifact.ArtifactType.CASES)
            .order_by("id")
            .first()
        )
        cases = _read_cases(artifact, limit + offset, status_filter=status_filter, category_filter=category_filter) if artifact else []
        return Response(
            {
                "run": run.id,
                "run_id": run.run_id,
                "limit": limit,
                "offset": offset,
                "cases": cases[offset : offset + limit],
            }
        )


class RunDLPFindingsView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request, pk):
        run = get_object_or_404(BenchmarkRun, pk=pk)
        limit = _parse_limit(request.query_params.get("limit"))
        findings = []
        for row in _run_case_rows(run, max_rows=1000):
            for finding in row.get("dlp_findings") or []:
                if isinstance(finding, dict):
                    findings.append({"case_id": row.get("case_id"), **finding})
                if len(findings) >= limit:
                    break
            if len(findings) >= limit:
                break
        return Response({"run": run.id, "run_id": run.run_id, "findings": findings})


class RunPolicyDecisionsView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request, pk):
        run = get_object_or_404(BenchmarkRun, pk=pk)
        limit = _parse_limit(request.query_params.get("limit"))
        decisions = []
        for row in _run_case_rows(run, max_rows=1000):
            for decision in row.get("policy_decisions") or []:
                if isinstance(decision, dict):
                    decisions.append({"case_id": row.get("case_id"), **decision})
                if len(decisions) >= limit:
                    break
            if len(decisions) >= limit:
                break
        return Response({"run": run.id, "run_id": run.run_id, "decisions": decisions})


def _completed_runs_with_metrics():
    return (
        BenchmarkRun.objects.filter(status=BenchmarkRun.Status.COMPLETED)
        .select_related("model_endpoint", "dataset", "defense_profile", "metrics")
        .filter(metrics__isnull=False)
        .order_by("-created_at", "-id")
    )


def _result_row(run):
    return {
        "run_id": run.run_id,
        "title": run.title,
        "model": _model_display_name(run.model_endpoint),
        "dataset": run.dataset.name,
        "defense_profile": run.defense_profile.name,
        "defense_level": run.defense_profile.level,
        "proxy_asr": run.metrics.proxy_asr,
        "one_minus_asr": run.metrics.one_minus_asr,
        "fpr": run.metrics.fpr,
        "u_mean": run.metrics.u_mean,
        "p95_latency": run.metrics.p95_latency,
        "parse_error_rate": run.metrics.parse_error_rate,
        "created_at": run.created_at,
    }


def _asr_by_profile(queryset):
    rows = (
        queryset.values("defense_profile__name", "defense_profile__level")
        .annotate(proxy_asr=Avg("metrics__proxy_asr"))
        .order_by("defense_profile__level", "defense_profile__name")
    )
    return [
        {
            "profile": row["defense_profile__name"],
            "defense_level": row["defense_profile__level"],
            "proxy_asr": row["proxy_asr"],
        }
        for row in rows
    ]


def _heatmap_rows(queryset):
    grouped: dict[tuple[str, str, str], list[float]] = {}
    for run in queryset.select_related("model_endpoint", "defense_profile", "metrics").filter(metrics__isnull=False):
        key = (
            _model_display_name(run.model_endpoint),
            run.defense_profile.name,
            run.defense_profile.level,
        )
        value = run.metrics.proxy_asr
        if value is not None:
            grouped.setdefault(key, []).append(value)
    return [
        {
            "model": model,
            "profile": profile,
            "defense_level": defense_level,
            "proxy_asr": sum(values) / len(values) if values else None,
        }
        for (model, profile, defense_level), values in sorted(grouped.items())
    ]


def _model_display_name(endpoint) -> str:
    endpoint_name = endpoint.name or ""
    model_name = endpoint.model_name or ""
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


def _resolve_artifact_path(artifact: RunArtifact) -> Path:
    path = Path(artifact.file_path)
    if path.is_absolute():
        return path
    return get_repo_root() / path


def _log_artifact(run: BenchmarkRun, name: str):
    artifact = (
        RunArtifact.objects.filter(run=run, file_path__iendswith=name)
        .order_by("id")
        .first()
    )
    if artifact:
        return artifact
    if run.output_dir:
        file_path = Path(run.output_dir) / name
        absolute_path = file_path if file_path.is_absolute() else get_repo_root() / file_path
        if absolute_path.is_file():
            return RunArtifact(run=run, artifact_type=RunArtifact.ArtifactType.LOG, file_path=str(file_path))
    return None


def _read_artifact_text(artifact: RunArtifact) -> str:
    path = _resolve_artifact_path(artifact)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _parse_limit(value) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return 100
    return max(1, min(limit, 1000))


def _parse_offset(value) -> int:
    try:
        offset = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(offset, 1000000))


def _read_cases(
    artifact: RunArtifact,
    limit: int,
    *,
    status_filter: str | None = None,
    category_filter: str | None = None,
) -> list[dict]:
    path = _resolve_artifact_path(artifact)
    if not path.is_file():
        return []
    cases = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if len(cases) >= limit:
                break
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                row = {"raw": line}
            if status_filter and row.get("status") != status_filter:
                continue
            if category_filter and row.get("category") != category_filter:
                continue
            cases.append(row)
    return cases


def _run_case_rows(run: BenchmarkRun, max_rows: int = 1000) -> list[dict]:
    artifact = (
        RunArtifact.objects.filter(run=run, artifact_type=RunArtifact.ArtifactType.CASES)
        .order_by("id")
        .first()
    )
    return _read_cases(artifact, max_rows) if artifact else []


def _read_progress(run: BenchmarkRun) -> dict:
    progress_path = None
    if run.output_dir:
        progress_path = get_repo_root() / run.output_dir / "progress.json"
    if progress_path and progress_path.is_file():
        try:
            data = json.loads(progress_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
    total = run.metrics.total_cases if hasattr(run, "metrics") else 0
    return {
        "done": total if run.status == BenchmarkRun.Status.COMPLETED else 0,
        "total": total,
        "status": run.status,
    }
