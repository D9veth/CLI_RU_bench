from apps.accounts.permissions import IsAdminRole, IsResearcherOrAdmin, IsViewerOrAbove


class RolePermissionViewSetMixin:
    read_actions = {"list", "retrieve"}
    write_actions = {"create", "update", "partial_update"}
    delete_actions = {"destroy"}

    def get_permissions(self):
        if self.action in self.read_actions:
            permission_classes = [IsViewerOrAbove]
        elif self.action in self.write_actions:
            permission_classes = [IsResearcherOrAdmin]
        elif self.action in self.delete_actions:
            permission_classes = [IsAdminRole]
        else:
            permission_classes = [IsViewerOrAbove]
        return [permission() for permission in permission_classes]
