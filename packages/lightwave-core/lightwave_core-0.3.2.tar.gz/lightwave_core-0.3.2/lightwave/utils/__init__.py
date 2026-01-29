"""Shared Django utilities for LightWave projects."""

# Note: BaseModel is intentionally not imported here to avoid
# AppRegistryNotReady errors. Import it from lightwave.utils.models directly.
from lightwave.utils.slug import (
    get_next_slug,
    get_next_unique_slug,
    get_next_unique_slug_value,
)
from lightwave.utils.timezones import get_common_timezones, get_timezones_display


def __getattr__(name):
    """Lazy import for BaseModel to avoid AppRegistryNotReady."""
    if name == "BaseModel":
        from lightwave.utils.models import BaseModel

        return BaseModel
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BaseModel",
    "get_common_timezones",
    "get_timezones_display",
    "get_next_unique_slug",
    "get_next_unique_slug_value",
    "get_next_slug",
]
