from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class BaseRoleTestCase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin1", password="pass12345", role=User.Role.ADMIN
        )
        self.manager1 = User.objects.create_user(
            username="mgr1", password="pass12345", role=User.Role.MANAGER
        )
        self.manager2 = User.objects.create_user(
            username="mgr2", password="pass12345", role=User.Role.MANAGER
        )
        self.user1 = User.objects.create_user(
            username="user1", password="pass12345", role=User.Role.USER, manager=self.manager1
        )
        self.user2 = User.objects.create_user(
            username="user2", password="pass12345", role=User.Role.USER, manager=self.manager2
        )

    def auth_as(self, user):
        self.client.force_authenticate(user=user)


class RegistrationTests(BaseRoleTestCase):
    def test_admin_can_register_user(self):
        self.auth_as(self.admin)
        resp = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "password": "somepass123",
                "role": User.Role.USER,
                "manager": self.manager1.id,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(username="newuser").manager, self.manager1)

    def test_manager_cannot_register_user(self):
        self.auth_as(self.manager1)
        resp = self.client.post(
            reverse("register"), {"username": "x", "password": "somepass123", "role": User.Role.USER}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_register_user(self):
        self.auth_as(self.user1)
        resp = self.client.post(
            reverse("register"), {"username": "x", "password": "somepass123", "role": User.Role.USER}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_role_rejects_manager_assignment(self):
        self.auth_as(self.admin)
        resp = self.client.post(
            reverse("register"),
            {
                "username": "mgr3",
                "password": "somepass123",
                "role": User.Role.MANAGER,
                "manager": self.manager2.id,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class UserListTests(BaseRoleTestCase):
    def test_admin_sees_all_users(self):
        self.auth_as(self.admin)
        resp = self.client.get(reverse("user-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], User.objects.count())

    def test_manager_sees_only_own_team(self):
        self.auth_as(self.manager1)
        resp = self.client.get(reverse("user-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        usernames = {u["username"] for u in resp.data["results"]}
        self.assertEqual(usernames, {"user1"})

    def test_user_cannot_list_users(self):
        self.auth_as(self.user1)
        resp = self.client.get(reverse("user-list"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class ProfileTests(BaseRoleTestCase):
    def test_user_can_view_and_update_own_profile(self):
        self.auth_as(self.user1)
        resp = self.client.get(reverse("profile"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "user1")

        resp = self.client.patch(reverse("profile"), {"first_name": "Updated"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.first_name, "Updated")

    def test_user_cannot_escalate_own_role_via_profile(self):
        self.auth_as(self.user1)
        resp = self.client.patch(reverse("profile"), {"role": User.Role.ADMIN})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.role, User.Role.USER)


class UserDetailTests(BaseRoleTestCase):
    def test_manager_can_view_own_team_member(self):
        self.auth_as(self.manager1)
        resp = self.client.get(reverse("user-detail", args=[self.user1.id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_manager_cannot_view_other_teams_member(self):
        self.auth_as(self.manager1)
        resp = self.client.get(reverse("user-detail", args=[self.user2.id]))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
