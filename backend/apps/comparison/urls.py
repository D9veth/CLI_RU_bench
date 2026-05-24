from django.urls import path

from apps.comparison.views import CompareOptionsView, CompareRunsCsvView, CompareRunsView


urlpatterns = [
    path("runs/", CompareRunsView.as_view(), name="compare-runs"),
    path("runs/export.csv", CompareRunsCsvView.as_view(), name="compare-runs-export"),
    path("options/", CompareOptionsView.as_view(), name="compare-options"),
]
