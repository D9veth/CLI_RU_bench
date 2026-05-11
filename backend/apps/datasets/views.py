from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.common.viewsets import RolePermissionViewSetMixin
from apps.datasets.models import Dataset
from apps.datasets.serializers import DatasetSerializer


class DatasetViewSet(RolePermissionViewSetMixin, viewsets.ModelViewSet):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer

    def destroy(self, request, *args, **kwargs):
        dataset = self.get_object()
        dataset.is_active = False
        dataset.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
