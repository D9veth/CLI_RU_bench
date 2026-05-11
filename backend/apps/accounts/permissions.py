from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.role == User.Role.ADMIN)
        )


class IsResearcherOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        allowed_roles = {User.Role.RESEARCHER, User.Role.ADMIN}
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.role in allowed_roles)
        )


class IsViewerOrAbove(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        allowed_roles = {User.Role.VIEWER, User.Role.RESEARCHER, User.Role.ADMIN}
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.role in allowed_roles)
        )
