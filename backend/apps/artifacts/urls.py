from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.artifacts.views import ProjectArtifactViewSet, RunArtifactViewSet, RunArtifactsByRunView


router = DefaultRouter()
router.register("artifacts", RunArtifactViewSet, basename="artifact")
router.register("project-artifacts", ProjectArtifactViewSet, basename="project-artifact")

urlpatterns = [
    path("", include(router.urls)),
    path("runs/<int:pk>/artifacts/", RunArtifactsByRunView.as_view(), name="run-artifacts"),
]
