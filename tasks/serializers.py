from rest_framework import serializers

from accounts.models import User

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True, default=None)

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "status",
            "assigned_to",
            "assigned_to_username",
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def validate_assigned_to(self, assigned_to):
        request = self.context["request"]
        user = request.user

        if user.role == User.Role.ADMIN:
            return assigned_to
        if user.role == User.Role.MANAGER:
            if assigned_to.id == user.id or assigned_to.manager_id == user.id:
                return assigned_to
            raise serializers.ValidationError("You may only assign tasks to yourself or your team members.")
        # USER role
        if assigned_to.id != user.id:
            raise serializers.ValidationError("You may only assign tasks to yourself.")
        return assigned_to

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
