"""Base agent factory and shared utilities for Pydantic AI agents.

This module provides common utilities that can be shared across all LightWave domains:
- Message format conversion (OpenAI -> Pydantic AI)
- Agent execution helpers (sync and streaming)
- Common system prompt functions
- Agent factory function
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.utils import timezone
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.toolsets import AbstractToolset

from lightwave.ai.types import UserDependencies

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


# =============================================================================
# System Prompt Helpers
# =============================================================================


async def add_user_name(ctx: RunContext[UserDependencies]) -> str:
    """Add user's display name to agent context.

    Args:
        ctx: Run context with user dependencies.

    Returns:
        String describing the user's name.
    """
    return f"The user's name is {ctx.deps.user.get_display_name()}"


async def add_user_email(ctx: RunContext[UserDependencies]) -> str:
    """Add user's email to agent context.

    Args:
        ctx: Run context with user dependencies.

    Returns:
        String describing the user's email.
    """
    return f"The user's email is {ctx.deps.user.email}"


async def current_datetime(ctx: RunContext[UserDependencies]) -> str:
    """Add current datetime to agent context.

    Args:
        ctx: Run context (unused but required by pydantic-ai).

    Returns:
        String describing the current datetime.
    """
    return f"The current datetime is {timezone.now()}"


# =============================================================================
# Message Conversion
# =============================================================================


def convert_openai_to_pydantic_messages(
    openai_messages: list[dict[str, Any]],
) -> list[ModelMessage]:
    """Convert OpenAI-style messages to Pydantic AI ModelMessage format.

    Args:
        openai_messages: List of message dicts with 'role' and 'content' keys.
            Supported roles: 'user', 'assistant', 'system', 'developer'

    Returns:
        List of Pydantic AI ModelMessage objects.
    """
    pydantic_messages: list[ModelMessage] = []

    for msg in openai_messages:
        role = msg.get("role")
        content = msg.get("content", "")

        if role == "user":
            pydantic_messages.append(ModelRequest(parts=[UserPromptPart(content=content)]))
        elif role == "assistant":
            pydantic_messages.append(ModelResponse(parts=[TextPart(content=content)]))
        elif role in ("system", "developer"):
            pydantic_messages.append(ModelRequest(parts=[SystemPromptPart(content=content)]))

    return pydantic_messages


# =============================================================================
# Agent Execution
# =============================================================================


async def run_agent(
    agent: Agent[UserDependencies, str],
    user: AbstractUser,
    message: str,
    message_history: list[dict[str, Any]] | None = None,
    event_stream_handler: Callable | None = None,
    tenant_schema: str | None = None,
) -> str:
    """Run an agent and return the response.

    Args:
        agent: The Pydantic AI agent to run.
        user: The authenticated Django user making the request.
        message: The user's message to process.
        message_history: Optional list of previous messages in OpenAI format.
        event_stream_handler: Optional handler for agent events.
        tenant_schema: Optional PostgreSQL schema for multi-tenant queries.
            Tools can access this via ctx.deps.tenant_schema.

    Returns:
        The agent's text response.
    """
    deps = UserDependencies(user=user, tenant_schema=tenant_schema)
    pydantic_messages = convert_openai_to_pydantic_messages(message_history) if message_history else None
    result = await agent.run(
        message,
        message_history=pydantic_messages,
        deps=deps,
        event_stream_handler=event_stream_handler,
    )
    return result.output


async def run_agent_streaming(
    agent: Agent[UserDependencies, str],
    user: AbstractUser,
    message: str,
    message_history: list[dict[str, Any]] | None = None,
    event_stream_handler: Callable | None = None,
    tenant_schema: str | None = None,
) -> AsyncIterator[str]:
    """Run an agent and stream the response.

    Args:
        agent: The Pydantic AI agent to run.
        user: The authenticated Django user making the request.
        message: The user's message to process.
        message_history: Optional list of previous messages in OpenAI format.
        event_stream_handler: Optional handler for agent events.
        tenant_schema: Optional PostgreSQL schema for multi-tenant queries.
            Tools can access this via ctx.deps.tenant_schema.

    Yields:
        Text chunks as they are generated by the agent.
    """
    deps = UserDependencies(user=user, tenant_schema=tenant_schema)
    pydantic_messages = convert_openai_to_pydantic_messages(message_history) if message_history else None
    async with agent.run_stream(
        message,
        message_history=pydantic_messages,
        deps=deps,
        event_stream_handler=event_stream_handler,
    ) as result:
        async for text in result.stream_text():
            yield text


# =============================================================================
# Agent Factory
# =============================================================================


def create_agent(
    toolsets: list[AbstractToolset],
    instructions: list[str | Callable] | None = None,
    model: str | None = None,
    retries: int = 2,
) -> Agent[UserDependencies, str]:
    """Create a Pydantic AI agent with standard configuration.

    This factory function creates agents with sensible defaults used across
    all LightWave domains. Domain-specific behavior can be customized via
    the instructions parameter.

    Args:
        toolsets: List of toolsets the agent can use.
        instructions: Optional list of system prompts or prompt functions.
            If None, uses default prompts (user name, email, datetime).
        model: Optional model name. Defaults to settings.DEFAULT_AGENT_MODEL.
        retries: Number of retries for failed tool calls. Default is 2.

    Returns:
        Configured Pydantic AI Agent instance.

    Example:
        >>> from lightwave.ai.tools import weather_toolset
        >>> agent = create_agent([weather_toolset])
        >>> # Or with custom instructions:
        >>> agent = create_agent(
        ...     [weather_toolset],
        ...     instructions=["You are a weather expert.", add_user_name]
        ... )
    """
    if instructions is None:
        instructions = [add_user_name, add_user_email, current_datetime]

    agent_model = model or getattr(settings, "DEFAULT_AGENT_MODEL", "openai:gpt-4o")

    return Agent(
        agent_model,
        toolsets=toolsets,
        instructions=instructions,
        retries=retries,
        deps_type=UserDependencies,
    )
