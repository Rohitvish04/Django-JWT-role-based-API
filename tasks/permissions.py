from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import User


class TaskPermission(BasePermission):
    """
    List/Create: Admin, Manager, User (queryset is filtered separately per role).
    Retrieve/Update: Admin, the assigned owner, or that owner's Manager.
    Delete: Admin only.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role == User.Role.ADMIN:
            return True

        if request.method == "DELETE":
            return False

        is_owner = obj.assigned_to_id == user.id
        is_owners_manager = user.role == User.Role.MANAGER and obj.assigned_to.manager_id == user.id

        if request.method in SAFE_METHODS:
            return is_owner or is_owners_manager

        # PUT/PATCH
        return is_owner or is_owners_manager
