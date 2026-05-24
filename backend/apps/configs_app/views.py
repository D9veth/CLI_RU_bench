from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsViewerOrAbove
from apps.common.viewsets import RolePermissionViewSetMixin
from apps.configs_app.models import DefenseProfile, ModelEndpoint
from apps.configs_app.serializers import DefenseProfileSerializer, ModelEndpointSerializer


class DefenseProfileViewSet(RolePermissionViewSetMixin, viewsets.ModelViewSet):
    queryset = DefenseProfile.objects.all()
    serializer_class = DefenseProfileSerializer

    def destroy(self, request, *args, **kwargs):
        defense_profile = self.get_object()
        defense_profile.is_active = False
        defense_profile.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ModelEndpointViewSet(RolePermissionViewSetMixin, viewsets.ModelViewSet):
    queryset = ModelEndpoint.objects.all()
    serializer_class = ModelEndpointSerializer

    def destroy(self, request, *args, **kwargs):
        model_endpoint = self.get_object()
        model_endpoint.is_active = False
        model_endpoint.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def preflight(self, request, pk=None):
        endpoint = self.get_object()
        return Response(
            {
                "ok": bool(endpoint.base_url and endpoint.model_name),
                "endpoint": endpoint.id,
                "model": endpoint.model_name,
                "base_url": endpoint.base_url,
                "message": "Endpoint configuration is present. Live network preflight runs through CLI.",
            }
        )


class ConfigValidateView(APIView):
    permission_classes = [IsViewerOrAbove]

    def post(self, request):
        from bench.core.config import RunConfig

        try:
            RunConfig.model_validate(request.data)
        except Exception as exc:
            return Response({"ok": False, "detail": str(exc)}, status=400)
        return Response({"ok": True})
