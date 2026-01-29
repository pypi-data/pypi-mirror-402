"""Base model with common timestamp fields and enforced validation."""

from django.db import models


class BaseModel(models.Model):
    """
    Base model that includes default created / updated timestamps.

    All LightWave Django models should extend this class.

    Validation is enforced on every save() by calling full_clean().
    This ensures Django's built-in field validators (EmailField, URLField, etc.)
    always run, not just when using ModelForms.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Override save to enforce validation on every save."""
        self.full_clean()
        super().save(*args, **kwargs)
