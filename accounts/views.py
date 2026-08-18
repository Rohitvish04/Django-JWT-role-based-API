from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import User
from .permissions import IsAdmin, IsAdminOrManager
from .serializers import RegisterSerializer, UserProfileSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """POST /api/register/ — Admin only. Creates a user and assigns their role
    (and, for role=USER, their manager)."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [IsAdmin]


class UserListView(generics.ListAPIView):
    """GET /api/users/
    Admin: every user. Manager: only their own team members. User: forbidden —
    users may only see themselves, via /api/profile/.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAdminOrManager]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return User.objects.all().order_by("id")
        return User.objects.filter(manager=user).order_by("id")


class UserDetailView(generics.RetrieveAPIView):
    """GET /api/users/{id}/
    Admin: any user. Manager: only members of their own team. User: not
    permitted (use /api/profile/ for their own record).
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return obj
        if user.role == User.Role.MANAGER and obj.manager_id == user.id:
            return obj
        raise PermissionDenied("You do not have permission to view this user.")


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PUT/PATCH /api/profile/ — every role manages their own profile."""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
