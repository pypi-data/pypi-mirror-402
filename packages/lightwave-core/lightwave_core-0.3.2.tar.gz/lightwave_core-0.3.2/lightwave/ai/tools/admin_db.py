"""Admin database tools for Pydantic AI agents using the MCP postgres server.

This module provides admin-only access to the postgres database through the MCP alchemy server.
Requires superuser permissions via the process_tool_call callback.
"""

from functools import lru_cache


def get_database_url() -> str:
    """Convert Django DATABASES setting back to a connection string.

    Returns:
        Database URL string suitable for SQLAlchemy/MCP connections.
    """
    from django.conf import settings

    db_config = settings.DATABASES["default"]

    engine = db_config["ENGINE"]
    name = db_config["NAME"]
    user = db_config["USER"]
    password = db_config["PASSWORD"]
    host = db_config["HOST"]
    port = db_config["PORT"]

    # Map Django engines to URL schemes
    if "postgresql" in engine:
        scheme = "postgresql"
    elif "mysql" in engine:
        scheme = "mysql"
    elif "sqlite" in engine:
        return f"sqlite:///{name}"
    else:
        scheme = "postgresql"  # default fallback

    return f"{scheme}://{user}:{password}@{host}:{port}/{name}"


@lru_cache(maxsize=1)
def get_admin_db():
    """Get the admin database MCP server instance.

    Lazily initialized to avoid import-time Django settings access.
    Cached for reuse across agent invocations.

    Returns:
        MCPServerStdio configured for PostgreSQL access.
    """
    from pydantic_ai.mcp import MCPServerStdio

    from lightwave.ai.permissions import tool_requires_superuser

    return MCPServerStdio(
        command="uvx",
        args=[
            "--from",
            "mcp-alchemy==2025.8.15.91819",
            "--with",
            "psycopg2-binary",
            "--refresh-package",
            "mcp-alchemy",
            "mcp-alchemy",
        ],
        env={
            "DB_URL": get_database_url(),
        },
        process_tool_call=tool_requires_superuser,
    )


# For backwards compatibility, expose as property-like access
# Usage: from lightwave.ai.tools import admin_db; agent = Agent(toolsets=[admin_db])
class _AdminDbProxy:
    """Proxy that lazily initializes the admin_db on first access."""

    _instance = None

    def __getattr__(self, name):
        if self._instance is None:
            self._instance = get_admin_db()
        return getattr(self._instance, name)

    def __repr__(self):
        return "<AdminDbProxy (lazy-loaded MCPServerStdio)>"


admin_db = _AdminDbProxy()
