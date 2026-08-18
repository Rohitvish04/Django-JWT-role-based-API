from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def assign_default_role(sender, instance, **kwargs):
    """Ensure every user always has a valid role before being saved,
    defaulting new/blank accounts to the least-privileged USER role."""
    if not instance.role:
        instance.role = sender.Role.USER
