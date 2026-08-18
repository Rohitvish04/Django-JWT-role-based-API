from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    manager_username = serializers.CharField(source="manager.username", read_only=True, default=None)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "manager",
            "manager_username",
            "date_joined",
        )
        read_only_fields = ("id", "date_joined")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.MANAGER), required=False, allow_null=True
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "role",
            "manager",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        role = attrs.get("role", User.Role.USER)
        manager = attrs.get("manager")
        if role != User.Role.USER and manager is not None:
            raise serializers.ValidationError(
                {"manager": "Only accounts with role=USER may be assigned to a manager."}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Used by a user to view/update their own profile. Role and team
    assignment are managed by Admins only, so they stay read-only here."""

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role", "manager")
        read_only_fields = ("id", "username", "role", "manager")
