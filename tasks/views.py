from django.db.models import Q
from rest_framework import viewsets

from accounts.models import User

from .models import Task
from .permissions import TaskPermission
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    """
    GET  /api/tasks/        - Admin: all tasks. Manager: own + team's tasks. User: own tasks only.
    POST /api/tasks/        - Admin, Manager, User (assignment is validated per role in the serializer).
    PUT/PATCH /api/tasks/{id}/ - Admin, the task owner, or the owner's Manager.
    DELETE /api/tasks/{id}/    - Admin only.
    """

    serializer_class = TaskSerializer
    permission_classes = [TaskPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return Task.objects.all()
        if user.role == User.Role.MANAGER:
            return Task.objects.filter(Q(assigned_to=user) | Q(assigned_to__manager=user))
        return Task.objects.filter(assigned_to=user)
