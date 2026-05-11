from rest_framework import status, viewsets
from rest_framework.response import Response

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
