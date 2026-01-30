"""Agents Service MCP Server.

This module provides the MCP server for the agents service using the
generic MCPServerFactory. It registers itself with the service registry
for CLI discovery.

Uses spec-driven mode: catalog derived from OpenAPI spec with overrides.
No explicit catalog file needed - endpoints are discovered from the API spec.
"""

import asyncio

import structlog
from fastmcp import FastMCP

from yirifi_mcp.catalog.base import Tier
from yirifi_mcp.catalog.overrides.agents import (
    DESCRIPTION_OVERRIDES,
    DIRECT_ENDPOINTS,
    EXCLUDE_PATTERNS,
    IDEMPOTENT_OVERRIDES,
    NAME_OVERRIDES,
    RISK_OVERRIDES,
)
from yirifi_mcp.core.config import AgentsServiceConfig
from yirifi_mcp.core.decorators import register_service
from yirifi_mcp.server.factory import MCPServerFactory

logger = structlog.get_logger()


@register_service(
    "agents",
    description="Agents service MCP server",
    urls={
        "local": "http://localhost:5016",
        "dev": "https://dev.agents.ops.yirifi.ai",
        "prd": "https://agents.ops.yirifi.ai",
    },
    tags=["core", "agents"],
    catalog_mode="spec-driven",
    overrides_module="yirifi_mcp.catalog.overrides.agents",
)
async def create_agents_server(config: AgentsServiceConfig | None = None) -> FastMCP:
    """Create agents service MCP server using spec-driven catalog.

    This factory function is registered with the service registry
    and can be invoked via CLI: yirifi-ops-mcp-hub -s agents

    The catalog is derived from the OpenAPI spec with minimal overrides,
    eliminating manual endpoint definitions while maintaining safety.

    Args:
        config: Optional config override. If not provided, creates default config.

    Returns:
        Configured FastMCP server instance
    """
    if config is None:
        config = AgentsServiceConfig()

    factory = MCPServerFactory(
        config=config,
        gateway_prefix="agents",  # Creates agents_api_catalog and agents_api_call
        # Spec-driven mode: derive catalog from OpenAPI spec with these overrides
        tier_overrides={ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS},
        risk_overrides=RISK_OVERRIDES,
        name_overrides=NAME_OVERRIDES,
        description_overrides=DESCRIPTION_OVERRIDES,
        idempotent_overrides=IDEMPOTENT_OVERRIDES,
        exclude_patterns=EXCLUDE_PATTERNS,
    )
    return await factory.build()


async def create_agents_server_with_lifespan():
    """Create agents server with proper resource lifecycle.

    Use this when you need automatic cleanup of HTTP clients.

    Example:
        >>> async with create_agents_server_with_lifespan() as mcp:
        ...     mcp.run()
    """
    config = AgentsServiceConfig()
    factory = MCPServerFactory(
        config=config,
        gateway_prefix="agents",
        tier_overrides={ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS},
        risk_overrides=RISK_OVERRIDES,
        exclude_patterns=EXCLUDE_PATTERNS,
    )
    return factory.lifespan()


def main():
    """Entry point for running agents-service MCP server."""

    async def run():
        config = AgentsServiceConfig()
        factory = MCPServerFactory(
            config=config,
            gateway_prefix="agents",
            tier_overrides={ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS},
            risk_overrides=RISK_OVERRIDES,
            exclude_patterns=EXCLUDE_PATTERNS,
        )
        async with factory.lifespan() as mcp:
            mcp.run()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
