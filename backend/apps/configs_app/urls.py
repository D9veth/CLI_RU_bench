from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.configs_app.views import DefenseProfileViewSet, ModelEndpointViewSet


router = DefaultRouter()
router.register("defense-profiles", DefenseProfileViewSet, basename="defense-profile")
router.register("model-endpoints", ModelEndpointViewSet, basename="model-endpoint")

urlpatterns = [
    path("", include(router.urls)),
]
