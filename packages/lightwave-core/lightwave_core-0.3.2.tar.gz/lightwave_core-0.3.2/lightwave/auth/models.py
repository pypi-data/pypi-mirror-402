"""Base user model for LightWave Django projects."""

import hashlib
import uuid
from functools import cached_property

from allauth.account.models import EmailAddress
from django.contrib.auth.models import AbstractUser
from django.db import models


def get_avatar_filename(instance, filename: str) -> str:
    """
    Generate a random filename for avatar uploads.

    Prevents overwriting existing files and fixes caching issues.
    """
    extension = filename.split(".")[-1]
    return f"profile-pictures/{uuid.uuid4()}.{extension}"


class BaseCustomUser(AbstractUser):
    """
    Abstract base user model with common fields for all LightWave projects.

    Includes avatar, language, timezone, and Gravatar integration.

    Validation is enforced on every save() by calling full_clean().
    This ensures Django's built-in field validators (EmailField, etc.)
    always run, not just when using ModelForms.

    To use, create a CustomUser model in your project that inherits from this:

        from lightwave.auth import BaseCustomUser

        class CustomUser(BaseCustomUser):
            # Add any project-specific fields here
            pass
    """

    avatar = models.FileField(
        upload_to=get_avatar_filename,
        blank=True,
        validators=[],  # Add validate_profile_picture in subclass
    )
    google_avatar_url = models.URLField(
        blank=True,
        null=True,
        help_text="Avatar URL synced from Google OAuth profile",
    )
    language = models.CharField(max_length=10, blank=True, null=True)
    timezone = models.CharField(max_length=100, blank=True, default="")

    # Presence tracking
    is_online = models.BooleanField(
        default=False,
        db_default=False,  # Database-level default for raw SQL/bulk inserts in tests
        help_text="Whether the user currently has an active WebSocket connection",
    )
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time the user was active (updated on WebSocket disconnect)",
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Override save to enforce validation on every save."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name()} <{self.email or self.username}>"

    def get_display_name(self) -> str:
        """Return the user's full name, falling back to email or username."""
        if self.get_full_name().strip():
            return self.get_full_name()
        return self.email or self.username

    @property
    def avatar_url(self) -> str:
        """
        Return the avatar URL with fallback chain.

        Priority:
        1. User's uploaded avatar
        2. Google OAuth profile picture
        3. Gravatar identicon
        """
        if self.avatar:
            return self.avatar.url
        if self.google_avatar_url:
            return self.google_avatar_url
        return f"https://www.gravatar.com/avatar/{self.gravatar_id}?s=128&d=identicon"

    @property
    def gravatar_id(self) -> str:
        """Return the Gravatar hash for the user's email."""
        # https://en.gravatar.com/site/implement/hash/
        return hashlib.md5(self.email.lower().strip().encode("utf-8")).hexdigest()

    @cached_property
    def has_verified_email(self) -> bool:
        """Check if the user has at least one verified email address."""
        return EmailAddress.objects.filter(user=self, verified=True).exists()
