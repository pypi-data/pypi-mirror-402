"""Shared types for Pydantic AI agents.

This module provides common type definitions used across all LightWave AI agents.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model

    User = get_user_model()


@dataclass
class UserDependencies:
    """Dependencies injected into agent context.

    Attributes:
        user: The authenticated Django user making the request.
        tenant_schema: The PostgreSQL schema name for multi-tenant queries.
            Used by tools to set the correct schema context.
    """

    user: "User"
    tenant_schema: str | None = None
