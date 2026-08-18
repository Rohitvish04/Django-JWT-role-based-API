from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User

from .models import Task


class BaseTaskTestCase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin1", password="pass12345", role=User.Role.ADMIN)
        self.manager1 = User.objects.create_user(username="mgr1", password="pass12345", role=User.Role.MANAGER)
        self.manager2 = User.objects.create_user(username="mgr2", password="pass12345", role=User.Role.MANAGER)
        self.user1 = User.objects.create_user(
            username="user1", password="pass12345", role=User.Role.USER, manager=self.manager1
        )
        self.user2 = User.objects.create_user(
            username="user2", password="pass12345", role=User.Role.USER, manager=self.manager2
        )

        self.task_user1 = Task.objects.create(title="User1 task", assigned_to=self.user1, created_by=self.user1)
        self.task_user2 = Task.objects.create(title="User2 task", assigned_to=self.user2, created_by=self.user2)

    def auth_as(self, user):
        self.client.force_authenticate(user=user)


class TaskListTests(BaseTaskTestCase):
    def test_admin_sees_all_tasks(self):
        self.auth_as(self.admin)
        resp = self.client.get(reverse("task-list"))
        self.assertEqual(resp.data["count"], 2)

    def test_manager_sees_only_team_tasks(self):
        self.auth_as(self.manager1)
        resp = self.client.get(reverse("task-list"))
        titles = {t["title"] for t in resp.data["results"]}
        self.assertEqual(titles, {"User1 task"})

    def test_user_sees_only_own_tasks(self):
        self.auth_as(self.user1)
        resp = self.client.get(reverse("task-list"))
        titles = {t["title"] for t in resp.data["results"]}
        self.assertEqual(titles, {"User1 task"})


class TaskCreateTests(BaseTaskTestCase):
    def test_user_can_create_own_task(self):
        self.auth_as(self.user1)
        resp = self.client.post(reverse("task-list"), {"title": "New", "assigned_to": self.user1.id})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_user_cannot_create_task_for_other_user(self):
        self.auth_as(self.user1)
        resp = self.client.post(reverse("task-list"), {"title": "New", "assigned_to": self.user2.id})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_manager_can_create_task_for_team_member(self):
        self.auth_as(self.manager1)
        resp = self.client.post(reverse("task-list"), {"title": "New", "assigned_to": self.user1.id})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_manager_cannot_create_task_for_other_teams_member(self):
        self.auth_as(self.manager1)
        resp = self.client.post(reverse("task-list"), {"title": "New", "assigned_to": self.user2.id})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class TaskUpdateDeleteTests(BaseTaskTestCase):
    def test_owner_can_update_own_task(self):
        self.auth_as(self.user1)
        resp = self.client.patch(reverse("task-detail", args=[self.task_user1.id]), {"status": "DONE"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_manager_can_update_team_members_task(self):
        self.auth_as(self.manager1)
        resp = self.client.patch(reverse("task-detail", args=[self.task_user1.id]), {"status": "DONE"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_user_cannot_update_others_task(self):
        self.auth_as(self.user2)
        resp = self.client.patch(reverse("task-detail", args=[self.task_user1.id]), {"status": "DONE"})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_manager_cannot_update_other_teams_task(self):
        self.auth_as(self.manager1)
        resp = self.client.patch(reverse("task-detail", args=[self.task_user2.id]), {"status": "DONE"})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_only_admin_can_delete(self):
        self.auth_as(self.manager1)
        resp = self.client.delete(reverse("task-detail", args=[self.task_user1.id]))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        self.auth_as(self.admin)
        resp = self.client.delete(reverse("task-detail", args=[self.task_user1.id]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
