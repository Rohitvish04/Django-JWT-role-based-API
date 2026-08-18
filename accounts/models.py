from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MANAGER = "MANAGER", "Manager"
        USER = "USER", "User"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)

    # Self-referential "team" link: a User's manager must themselves hold the
    # MANAGER role. Only meaningful for role=USER; Managers/Admins leave this null.
    manager = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="team_members",
        limit_choices_to={"role": Role.MANAGER},
    )

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    def __str__(self):
        return f"{self.username} ({self.role})"
