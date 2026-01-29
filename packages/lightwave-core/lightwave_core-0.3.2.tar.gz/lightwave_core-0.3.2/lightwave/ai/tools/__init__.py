"""Shared AI tools for Pydantic AI agents.

This module provides common toolsets that can be used across all LightWave domains.
Domain-specific tools should remain in their respective domain apps.
"""

from lightwave.ai.tools.admin_db import admin_db, get_database_url
from lightwave.ai.tools.email import email_toolset
from lightwave.ai.tools.weather import weather_toolset

__all__ = [
    "weather_toolset",
    "email_toolset",
    "admin_db",
    "get_database_url",
]
