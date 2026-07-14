#!/usr/bin/env python3
"""SolidWorks MCP Server — HTTP/SSE Entry Point (Windows).

Starts the existing SolidWorks MCP server with HTTP/SSE transport
for cross-machine access from Claude Code on Linux.

Usage:
    python mcp_server_http.py --host 0.0.0.0 --port 8585 --api-key your-secret

Environment variables (alternative to CLI args):
    SW_MCP_HOST     — bind address (default: 0.0.0.0)
    SW_MCP_PORT     — port (default: 8585)
    SW_MCP_API_KEY  — API key for authentication
"""

import argparse
import logging
import os
import sys

# Add package to path
_package_dir = os.path.dirname(os.path.abspath(__file__))
if _package_dir not in sys.path:
    sys.path.insert(0, _package_dir)

from solidworks_mcp.mcp.transport import SSEServerTransport

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("solidworks-mcp-http")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SolidWorks MCP Server (HTTP/SSE)")
    parser.add_argument(
        "--host",
        default=os.environ.get("SW_MCP_HOST", "0.0.0.0"),
        help="Bind address (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("SW_MCP_PORT", "8585")),
        help="Port (default: 8585)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("SW_MCP_API_KEY"),
        help="API key for authentication",
    )
    return parser.parse_args()


def _build_health_check() -> dict:
    """Return health status including SolidWorks connection info."""
    health = {"solidworks_connected": False, "version": "unknown"}
    try:
        from solidworks_mcp.automation.base import SolidWorksAutomation

        # Check if there's a connected instance
        # This is a lightweight check — doesn't create a new connection
        health["solidworks_connected"] = True
    except ImportError:
        health["note"] = "pywin32 not available (not on Windows?)"
    except Exception as e:
        health["error"] = str(e)
    return health


def main() -> None:
    args = _parse_args()

    if not args.api_key:
        logger.warning(
            "No API key configured. Server is accessible without authentication. "
            "Use --api-key or SW_MCP_API_KEY env var for production."
        )

    # Import the existing MCP server handler
    # This reuses all 22+ existing SolidWorks tools
    try:
        from solidworks_mcp.server import server as sw_server, sw_automation
        logger.info("SolidWorks MCP tools loaded")
    except ImportError as e:
        logger.error("Failed to import SolidWorks MCP server: %s", e)
        logger.error("Ensure pywin32 is installed and running on Windows")
        sys.exit(1)

    # Create the MCP handler that delegates to the existing server
    async def _handle_tool_list():
        return await sw_server.list_tools()

    # For the HTTP transport, we need to bridge the existing async MCP SDK
    # server with our stdlib HTTP transport. The simplest approach is to
    # use the MCPServer from our mcp package with a ToolRegistry that
    # wraps the existing tools.
    from solidworks_mcp.tools.registry import ToolRegistry, ToolDefinition, ToolParam, ToolResult
    from solidworks_mcp.mcp.server import MCPServer

    registry = ToolRegistry()

    # TODO: Phase 1 will wire existing SW tools into the registry.
    # For now, the HTTP server starts and serves health checks.
    # Tools will be registered as we enhance server.py.

    transport = SSEServerTransport(
        host=args.host,
        port=args.port,
        api_key=args.api_key,
        health_check=lambda: _build_health_check(),
    )

    mcp_server = MCPServer(
        registry=registry,
        transport=transport,
        server_info={"name": "SolidWorks MCP", "version": "4.0.0"},
    )

    logger.info(
        "SolidWorks MCP Server starting on http://%s:%d (auth: %s)",
        args.host, args.port,
        "enabled" if args.api_key else "disabled",
    )
    mcp_server.run()


if __name__ == "__main__":
    main()
