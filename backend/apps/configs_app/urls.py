from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.configs_app.views import ConfigValidateView, DefenseProfileViewSet, ModelEndpointViewSet


router = DefaultRouter()
router.register("defense-profiles", DefenseProfileViewSet, basename="defense-profile")
router.register("model-endpoints", ModelEndpointViewSet, basename="model-endpoint")

urlpatterns = [
    path("configs/validate/", ConfigValidateView.as_view(), name="configs-validate"),
    path("", include(router.urls)),
]
