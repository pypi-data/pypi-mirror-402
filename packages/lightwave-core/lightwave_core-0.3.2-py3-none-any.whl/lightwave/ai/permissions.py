"""Permission helpers for Pydantic AI tool authorization.

This module provides permission checking utilities for MCP and function tools.
"""

from django.core.exceptions import PermissionDenied


def tool_requires_superuser(ctx, direct_call_tool, name, tool_args):
    """Check if the current user has admin access before executing a tool.

    This is designed to be used as the process_tool_call callback for
    MCPServerStdio instances that require elevated permissions.

    Args:
        ctx: The run context containing user dependencies.
        direct_call_tool: The tool function to call if authorized.
        name: Name of the tool being called.
        tool_args: Arguments for the tool call.

    Returns:
        The result of calling the tool if authorized.

    Raises:
        PermissionDenied: If user is not a superuser with staff status.
    """
    # Get user from the context dependencies
    user = ctx.deps.user if hasattr(ctx, "deps") and hasattr(ctx.deps, "user") else None

    if not user or not (user.is_superuser and user.is_staff):
        raise PermissionDenied("Admin access required for database operations")

    return direct_call_tool(name, tool_args)
