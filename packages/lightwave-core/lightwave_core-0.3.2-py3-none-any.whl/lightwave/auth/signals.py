"""User signal handlers for LightWave projects.

To use these signals, import and connect them in your project's apps.py:

    from django.apps import AppConfig

    class UsersConfig(AppConfig):
        name = "apps.users"

        def ready(self):
            from lightwave.auth.signals import connect_user_signals
            from apps.users.models import CustomUser
            connect_user_signals(CustomUser)
"""

from allauth.account.signals import email_confirmed, user_signed_up
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.mail import mail_admins
from django.db.models.signals import post_delete, pre_save


def handle_sign_up(request, user, **kwargs):
    """
    Handle user sign up event.

    By default, notifies admins of new signups.
    Override this in your project for custom behavior (e.g., welcome emails).
    """
    _notify_admins_of_signup(user)


def update_user_email(sender, request, email_address, **kwargs):
    """
    When an email address is confirmed, make it the primary email.

    This also updates user.email to the new email address.
    """
    email_address.set_as_primary()


def _notify_admins_of_signup(user):
    """Send an email to admins when a new user signs up."""
    project_name = getattr(settings, "PROJECT_METADATA", {}).get("NAME", "LightWave")
    mail_admins(
        f"Yowsers, someone signed up for {project_name}!",
        f"Email: {user.email}",
        fail_silently=True,
    )


def _make_remove_old_profile_picture_handler(user_model):
    """Create a signal handler for removing old profile pictures on change."""

    def remove_old_profile_picture_on_change(sender, instance, **kwargs):
        if not instance.pk:
            return False

        try:
            old_file = sender.objects.get(pk=instance.pk).avatar
        except sender.DoesNotExist:
            return False

        if old_file and old_file.name != instance.avatar.name and default_storage.exists(old_file.name):
            default_storage.delete(old_file.name)

    return remove_old_profile_picture_on_change


def _make_remove_profile_picture_on_delete_handler():
    """Create a signal handler for removing profile pictures on user delete."""

    def remove_profile_picture_on_delete(sender, instance, **kwargs):
        if instance.avatar and default_storage.exists(instance.avatar.name):
            default_storage.delete(instance.avatar.name)

    return remove_profile_picture_on_delete


def connect_user_signals(user_model):
    """
    Connect all user-related signals for a CustomUser model.

    Call this in your users app's AppConfig.ready() method:

        from lightwave.auth.signals import connect_user_signals
        from apps.users.models import CustomUser
        connect_user_signals(CustomUser)
    """
    # Allauth signals
    user_signed_up.connect(handle_sign_up)
    email_confirmed.connect(update_user_email)

    # Profile picture cleanup signals
    pre_save.connect(_make_remove_old_profile_picture_handler(user_model), sender=user_model)
    post_delete.connect(_make_remove_profile_picture_on_delete_handler(), sender=user_model)
