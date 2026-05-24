from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.experiments.views import (
    BenchmarkRunViewSet,
    DashboardView,
    HeatmapResultsView,
    ParetoResultsView,
    ResultsView,
    RunCasesView,
    RunDLPFindingsView,
    RunIngestView,
    RunMetricsByRunView,
    RunPolicyDecisionsView,
    RunMetricsViewSet,
    RunReportView,
)


router = DefaultRouter()
router.register("runs", BenchmarkRunViewSet, basename="run")
router.register("run-metrics", RunMetricsViewSet, basename="run-metrics")

urlpatterns = [
    path("runs/ingest/", RunIngestView.as_view(), name="runs-ingest"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("results/", ResultsView.as_view(), name="results"),
    path("results/pareto/", ParetoResultsView.as_view(), name="results-pareto"),
    path("results/heatmap/", HeatmapResultsView.as_view(), name="results-heatmap"),
    path("runs/<int:pk>/metrics/", RunMetricsByRunView.as_view(), name="run-metrics-detail"),
    path("runs/<int:pk>/report/", RunReportView.as_view(), name="run-report"),
    path("runs/<int:pk>/cases/", RunCasesView.as_view(), name="run-cases"),
    path("runs/<int:pk>/dlp-findings/", RunDLPFindingsView.as_view(), name="run-dlp-findings"),
    path("runs/<int:pk>/policy-decisions/", RunPolicyDecisionsView.as_view(), name="run-policy-decisions"),
    path("", include(router.urls)),
]
