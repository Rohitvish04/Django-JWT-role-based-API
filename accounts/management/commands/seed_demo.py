from django.core.management.base import BaseCommand

from accounts.models import User
from tasks.models import Task


class Command(BaseCommand):
    help = "Seed a sample team structure (1 admin, 2 managers, 4 users) and a few tasks for demoing the API."

    def handle(self, *args, **options):
        admin, created = User.objects.get_or_create(
            username="admin", defaults={"role": User.Role.ADMIN, "is_staff": True, "is_superuser": True}
        )
        if created:
            admin.set_password("AdminPass123")
            admin.save()

        mgr_sales, _ = User.objects.get_or_create(
            username="mgr_sales", defaults={"role": User.Role.MANAGER}
        )
        mgr_sales.set_password("MgrPass123")
        mgr_sales.save()

        mgr_support, _ = User.objects.get_or_create(
            username="mgr_support", defaults={"role": User.Role.MANAGER}
        )
        mgr_support.set_password("MgrPass123")
        mgr_support.save()

        sample_users = [
            ("alice", mgr_sales),
            ("bob", mgr_sales),
            ("carol", mgr_support),
            ("dave", mgr_support),
        ]
        created_users = {}
        for username, manager in sample_users:
            u, _ = User.objects.get_or_create(
                username=username, defaults={"role": User.Role.USER, "manager": manager}
            )
            u.set_password("UserPass123")
            u.manager = manager
            u.save()
            created_users[username] = u

        Task.objects.get_or_create(
            title="Follow up with lead",
            assigned_to=created_users["alice"],
            defaults={"created_by": mgr_sales, "description": "Call back the enterprise lead from Monday."},
        )
        Task.objects.get_or_create(
            title="Resolve ticket #482",
            assigned_to=created_users["carol"],
            defaults={"created_by": mgr_support, "description": "Customer reports login failure."},
        )

        self.stdout.write(self.style.SUCCESS(
            "Seeded: admin/AdminPass123, mgr_sales & mgr_support/MgrPass123, "
            "alice/bob/carol/dave/UserPass123 (alice,bob -> mgr_sales; carol,dave -> mgr_support)"
        ))
