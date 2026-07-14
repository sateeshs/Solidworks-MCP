#!/usr/bin/env python3
"""Parts Intelligence MCP Server (STDIO).

Lightweight MCP server that provides goBILDA part search, profile lookup,
compatibility queries, and mate suggestions. Runs on Linux as a STDIO
subprocess launched by Claude Code.

No SolidWorks dependency. No pywin32. Pure Python stdlib + JSON profiles.

Usage:
    # Direct test
    echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python parts_server.py

    # Claude Code config (~/.claude/mcp_servers.json):
    {
        "parts-intelligence": {
            "type": "stdio",
            "command": "python",
            "args": ["/path/to/Solidworks-MCP/parts_server.py"]
        }
    }
"""

import logging
import os
import sys

# Ensure package is importable
_package_dir = os.path.dirname(os.path.abspath(__file__))
if _package_dir not in sys.path:
    sys.path.insert(0, _package_dir)

from solidworks_mcp.tools.registry import ToolParam, ToolDefinition, ToolResult, ToolRegistry
from solidworks_mcp.mcp.server import MCPServer
from solidworks_mcp.mcp.transport import StdioServerTransport
from solidworks_mcp.parts.query import PartsQuery

# Configure logging to stderr (stdout is for MCP JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("parts-intelligence")

# Default profiles directory (relative to this script)
PROFILES_DIR = os.path.join(_package_dir, "profiles", "gobilda")

SERVER_INFO = {"name": "Parts Intelligence", "version": "1.0.0"}


def _create_query_engine() -> PartsQuery:
    """Initialize the parts query engine from profile data."""
    profiles_dir = os.environ.get("PARTS_PROFILES_DIR", PROFILES_DIR)
    engine = PartsQuery(profiles_dir)

    if os.path.isdir(profiles_dir):
        engine.load()
        logger.info("Parts query engine loaded: %d parts", engine.part_count)
    else:
        logger.warning(
            "Profiles directory not found: %s. "
            "Run scripts/analyze_gobilda_parts.py to generate profiles.",
            profiles_dir,
        )

    return engine


def _register_tools(registry: ToolRegistry, engine: PartsQuery) -> None:
    """Register all Parts Intelligence tools."""

    # --- search_parts ---
    def handle_search_parts(
        query: str,
        category: str | None = None,
        min_length: float | None = None,
        max_length: float | None = None,
        bolt_size: str | None = None,
        limit: int = 20,
    ) -> ToolResult:
        results = engine.search_parts(
            query=query,
            category=category,
            min_length=min_length,
            max_length=max_length,
            bolt_size=bolt_size,
            limit=limit,
        )
        if not results:
            return ToolResult(
                success=True,
                output=f"No parts found matching '{query}'",
                data={"results": [], "count": 0},
            )
        return ToolResult(
            success=True,
            output=f"Found {len(results)} parts matching '{query}'",
            data={"results": results, "count": len(results)},
        )

    registry.register(ToolDefinition(
        name="search_parts",
        description=(
            "Search goBILDA parts catalog by keyword. "
            "Returns SKU, name, dimensions, and category. "
            "Filter by category, length range, or bolt size."
        ),
        parameters=[
            ToolParam("query", "string", "Search keyword (e.g., 'mecanum wheel', 'U-Channel')"),
            ToolParam("category", "string", "Filter by category (e.g., 'motion/wheel')", required=False),
            ToolParam("min_length", "number", "Minimum length in mm", required=False),
            ToolParam("max_length", "number", "Maximum length in mm", required=False),
            ToolParam("bolt_size", "string", "Filter by bolt size (e.g., 'M4')", required=False),
            ToolParam("limit", "integer", "Max results (default 20)", required=False, default=20),
        ],
        handler=handle_search_parts,
        category="parts",
    ))

    # --- get_part_profile ---
    def handle_get_part_profile(sku: str) -> ToolResult:
        profile = engine.get_part_profile(sku)
        if not profile:
            return ToolResult(
                success=False, output="", error=f"Part not found: {sku}"
            )
        return ToolResult(
            success=True,
            output=f"Profile for {profile['name']} ({sku})",
            data=profile,
        )

    registry.register(ToolDefinition(
        name="get_part_profile",
        description=(
            "Get full semantic profile of a goBILDA part by SKU. "
            "Returns mounting faces, hole patterns, connection points, "
            "compatibility tags, and geometry details."
        ),
        parameters=[
            ToolParam("sku", "string", "goBILDA SKU (e.g., '1120-0001-0288')"),
        ],
        handler=handle_get_part_profile,
        category="parts",
    ))

    # --- find_compatible_parts ---
    def handle_find_compatible_parts(
        tag: str,
        category: str | None = None,
        limit: int = 20,
    ) -> ToolResult:
        results = engine.find_compatible_parts(tag=tag, category=category, limit=limit)
        if not results:
            return ToolResult(
                success=True,
                output=f"No parts found compatible with '{tag}'",
                data={"results": [], "count": 0},
            )
        return ToolResult(
            success=True,
            output=f"Found {len(results)} parts compatible with '{tag}'",
            data={"results": results, "count": len(results)},
        )

    registry.register(ToolDefinition(
        name="find_compatible_parts",
        description=(
            "Find parts compatible with a given tag. "
            "Tags include: gobilda_8mm_pattern, REX_8mm_shaft, "
            "M4_socket_head, yellow_jacket_motor_mount."
        ),
        parameters=[
            ToolParam("tag", "string", "Compatibility tag (e.g., 'REX_8mm_shaft')"),
            ToolParam("category", "string", "Filter by category", required=False),
            ToolParam("limit", "integer", "Max results (default 20)", required=False, default=20),
        ],
        handler=handle_find_compatible_parts,
        category="parts",
    ))

    # --- list_categories ---
    def handle_list_categories() -> ToolResult:
        categories = engine.list_categories()
        return ToolResult(
            success=True,
            output=f"{len(categories)} part categories available",
            data={"categories": categories, "count": len(categories)},
        )

    registry.register(ToolDefinition(
        name="list_categories",
        description=(
            "List all goBILDA part categories with part counts. "
            "Categories include structure/channel, motion/wheel, motion/motor, etc."
        ),
        parameters=[],
        handler=handle_list_categories,
        category="parts",
    ))

    # --- suggest_mates ---
    def handle_suggest_mates(sku_a: str, sku_b: str) -> ToolResult:
        suggestions = engine.suggest_mates(sku_a, sku_b)
        if not suggestions:
            return ToolResult(
                success=True,
                output=f"No mate suggestions between {sku_a} and {sku_b}",
                data={"suggestions": [], "count": 0},
            )
        return ToolResult(
            success=True,
            output=f"{len(suggestions)} mate suggestions between {sku_a} and {sku_b}",
            data={"suggestions": suggestions, "count": len(suggestions)},
        )

    registry.register(ToolDefinition(
        name="suggest_mates",
        description=(
            "Suggest mate constraints between two goBILDA parts based on their profiles. "
            "Returns mate type (coincident, concentric, distance), reference faces, "
            "and confidence score."
        ),
        parameters=[
            ToolParam("sku_a", "string", "First part SKU"),
            ToolParam("sku_b", "string", "Second part SKU"),
        ],
        handler=handle_suggest_mates,
        category="parts",
    ))


def main() -> None:
    """Entry point for Parts Intelligence server."""
    engine = _create_query_engine()

    registry = ToolRegistry()
    _register_tools(registry, engine)

    server = MCPServer(
        registry=registry,
        transport=StdioServerTransport(),
        server_info=SERVER_INFO,
    )

    logger.info("Parts Intelligence server starting (%d tools)", len(registry.list_tools()))
    server.run()


if __name__ == "__main__":
    main()
