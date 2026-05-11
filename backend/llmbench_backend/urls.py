from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", include("apps.common.urls")),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.datasets.urls")),
    path("api/", include("apps.configs_app.urls")),
    path("api/", include("apps.experiments.urls")),
    path("api/", include("apps.artifacts.urls")),
]
