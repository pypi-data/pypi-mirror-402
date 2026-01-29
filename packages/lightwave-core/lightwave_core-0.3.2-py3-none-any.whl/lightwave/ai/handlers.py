"""Event handlers for Pydantic AI agent execution.

This module provides handlers for logging and debugging agent events.
"""

import logging
from collections.abc import AsyncIterable

from pydantic_ai.messages import (
    AgentStreamEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
)

logger = logging.getLogger("lightwave.ai")


async def agent_event_stream_handler(ctx, event_stream: AsyncIterable[AgentStreamEvent]):
    """Handle and log agent execution events for debugging.

    This handler logs tool calls and their results at DEBUG level,
    useful for tracing agent execution flow.

    Args:
        ctx: The run context (unused but required by pydantic-ai).
        event_stream: Async stream of agent events to process.
    """
    async for event in event_stream:
        if isinstance(event, FunctionToolCallEvent):
            logger.debug(f"LLM calls tool={event.part.tool_name!r} with args={event.part.args}")
        elif isinstance(event, FunctionToolResultEvent):
            logger.debug(f"Tool call {event.tool_call_id!r} returned => {event.result.content}")
