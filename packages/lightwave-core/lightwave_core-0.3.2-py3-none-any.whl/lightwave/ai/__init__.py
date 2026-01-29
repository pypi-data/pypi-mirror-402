"""LightWave AI - Shared AI agents and utilities for LightWave Media projects.

This module provides:
- Brand context and voice models for copywriting
- Copywriter agent factory
- Shared tools (weather, email, admin_db)
- Permission helpers and event handlers
- Common types for agent dependencies
- Base agent factory and utilities
"""

from lightwave.ai.base import (
    add_user_email,
    add_user_name,
    convert_openai_to_pydantic_messages,
    create_agent,
    current_datetime,
    run_agent,
    run_agent_streaming,
)
from lightwave.ai.brand_context import (
    BrandContext,
    VoiceModel,
    get_brand_context,
)
from lightwave.ai.copywriter import (
    COPYWRITER_SYSTEM_PROMPT,
    get_copywriter_agent,
)
from lightwave.ai.handlers import agent_event_stream_handler
from lightwave.ai.permissions import tool_requires_superuser
from lightwave.ai.types import UserDependencies

__all__ = [
    # Brand & Copywriter
    "BrandContext",
    "VoiceModel",
    "get_brand_context",
    "COPYWRITER_SYSTEM_PROMPT",
    "get_copywriter_agent",
    # Shared infrastructure
    "UserDependencies",
    "tool_requires_superuser",
    "agent_event_stream_handler",
    # Base utilities
    "add_user_name",
    "add_user_email",
    "current_datetime",
    "convert_openai_to_pydantic_messages",
    "run_agent",
    "run_agent_streaming",
    "create_agent",
]
