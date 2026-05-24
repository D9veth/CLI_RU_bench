from django.contrib import admin
from django.urls import include, path
from apps.common.views import ReadyView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", include("apps.common.urls")),
    path("api/ready/", ReadyView.as_view(), name="ready"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.datasets.urls")),
    path("api/", include("apps.configs_app.urls")),
    path("api/", include("apps.experiments.urls")),
    path("api/", include("apps.artifacts.urls")),
    path("api/compare/", include("apps.comparison.urls")),
]
