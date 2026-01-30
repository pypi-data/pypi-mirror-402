"""MCP Server entry point"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from mcp.server.fastmcp import FastMCP

from mcp_server.database.connection import DatabasePool
from mcp_server.prompts import register_prompts
from mcp_server.resources import register_resources
from mcp_server.tools import register_tools
from mcp_server.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncGenerator[None, None]:
    """Application lifecycle management

    Handles startup and shutdown of resources like database connections.
    """
    setup_logging()
    logger.info("mcp_server_starting", server_name=server.name)

    try:
        # Initialize database pool
        await DatabasePool.init()
        logger.info("mcp_server_ready")
        yield
    finally:
        # Cleanup
        await DatabasePool.close()
        logger.info("mcp_server_stopped")


# Create MCP server instance
mcp = FastMCP(
    name="ecs-contract-mcp",
    lifespan=app_lifespan,
)

# Register all Resources, Tools, and Prompts
register_resources(mcp)
register_tools(mcp)
register_prompts(mcp)


# Health check tool (useful for testing connectivity)
@mcp.tool()
async def health_check() -> dict:
    """Check MCP server health and database connectivity

    Returns:
        Health status including database pool status
    """
    pool_status = DatabasePool.pool_status()
    return {
        "status": "healthy" if pool_status["initialized"] else "unhealthy",
        "database": pool_status,
    }


def main() -> None:
    """Main entry point"""
    mcp.run()


if __name__ == "__main__":
    main()
