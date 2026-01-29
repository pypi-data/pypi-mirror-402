"""Django app configuration for LightWave security."""

from django.apps import AppConfig


class SecurityConfig(AppConfig):
    """Configuration for the lightwave.security app."""

    name = "lightwave.security"
    verbose_name = "LightWave Security"
    default_auto_field = "django.db.models.BigAutoField"
