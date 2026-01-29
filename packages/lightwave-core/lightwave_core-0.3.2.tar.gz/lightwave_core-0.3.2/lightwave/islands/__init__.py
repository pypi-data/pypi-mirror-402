"""LightWave Islands - Shared Django templates and context processors for React islands."""

from lightwave.islands.middleware import SiteMiddleware, get_current_site

default_app_config = "lightwave.islands.apps.IslandsConfig"

__all__ = [
    "SiteMiddleware",
    "get_current_site",
]
