"""HyperX MCP Server implementation."""

import asyncio
import json
import os
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

from hyperxdb import HyperX
from hyperxdb.agents import create_tools

# Create MCP server instance
server = Server("hyperx-mcp")

# Global client and tools (initialized on startup)
_client: HyperX | None = None
_tools: Any = None


def get_client() -> HyperX:
    """Get or create the HyperX client."""
    global _client
    if _client is None:
        base_url = os.environ.get("HYPERX_BASE_URL", "https://api.hyperxdb.dev")
        api_key = os.environ.get("HYPERX_API_KEY")
        if not api_key:
            raise ValueError("HYPERX_API_KEY environment variable is required")
        _client = HyperX(base_url=base_url, api_key=api_key)
    return _client


def get_tools():
    """Get or create the HyperX tools."""
    global _tools
    if _tools is None:
        access_level = os.environ.get("HYPERX_ACCESS_LEVEL", "explore")
        _tools = create_tools(get_client(), access_level=access_level)
    return _tools


# Tool definitions for MCP
TOOL_DEFINITIONS = [
    {
        "name": "hyperx_search",
        "description": "Search the knowledge graph using hybrid (vector + text) search. Returns entities matching the query with relevance scores.",
        "parameters": {
            "query": {"type": "string", "description": "Search query text", "required": True},
            "limit": {"type": "integer", "description": "Maximum results to return (default: 10)", "required": False},
            "entity_types": {"type": "array", "items": {"type": "string"}, "description": "Filter by entity types", "required": False},
        },
    },
    {
        "name": "hyperx_lookup",
        "description": "Look up a specific entity by its ID. Returns full entity details including attributes and description.",
        "parameters": {
            "entity_id": {"type": "string", "description": "The entity ID to look up", "required": True},
        },
    },
    {
        "name": "hyperx_paths",
        "description": "Find connection paths between two entities in the knowledge graph. Useful for understanding how concepts relate.",
        "parameters": {
            "source_id": {"type": "string", "description": "Source entity ID", "required": True},
            "target_id": {"type": "string", "description": "Target entity ID", "required": True},
            "max_hops": {"type": "integer", "description": "Maximum path length (default: 4)", "required": False},
        },
    },
    {
        "name": "hyperx_explorer",
        "description": "Explore the neighborhood of an entity - find connected entities and relationships within a specified depth.",
        "parameters": {
            "entity_id": {"type": "string", "description": "Entity ID to explore from", "required": True},
            "depth": {"type": "integer", "description": "Exploration depth (default: 2)", "required": False},
            "max_entities": {"type": "integer", "description": "Maximum entities to return (default: 50)", "required": False},
        },
    },
    {
        "name": "hyperx_explain",
        "description": "Get a natural language explanation of an entity and its context in the knowledge graph.",
        "parameters": {
            "entity_id": {"type": "string", "description": "Entity ID to explain", "required": True},
        },
    },
    {
        "name": "hyperx_relationships",
        "description": "Get all relationships (hyperedges) that an entity participates in.",
        "parameters": {
            "entity_id": {"type": "string", "description": "Entity ID", "required": True},
            "relationship_types": {"type": "array", "items": {"type": "string"}, "description": "Filter by relationship types", "required": False},
        },
    },
    {
        "name": "hyperx_entity_crud",
        "description": "Create, update, or delete entities in the knowledge graph. Requires 'full' access level.",
        "parameters": {
            "operation": {"type": "string", "enum": ["create", "update", "delete"], "description": "Operation to perform", "required": True},
            "entity_id": {"type": "string", "description": "Entity ID (for update/delete)", "required": False},
            "label": {"type": "string", "description": "Entity label (for create)", "required": False},
            "entity_type": {"type": "string", "description": "Entity type (for create)", "required": False},
            "description": {"type": "string", "description": "Entity description", "required": False},
            "attributes": {"type": "object", "description": "Entity attributes", "required": False},
        },
    },
    {
        "name": "hyperx_hyperedge_crud",
        "description": "Create, update, or delete hyperedges (relationships) in the knowledge graph. Requires 'full' access level.",
        "parameters": {
            "operation": {"type": "string", "enum": ["create", "update", "delete"], "description": "Operation to perform", "required": True},
            "hyperedge_id": {"type": "string", "description": "Hyperedge ID (for update/delete)", "required": False},
            "edge_type": {"type": "string", "description": "Relationship type (for create)", "required": False},
            "members": {"type": "array", "description": "List of {entity_id, role} members", "required": False},
            "attributes": {"type": "object", "description": "Hyperedge attributes", "required": False},
        },
    },
]


@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List available HyperX tools."""
    tools = []
    for defn in TOOL_DEFINITIONS:
        # Convert parameters to MCP format
        properties = {}
        required = []
        for name, spec in defn["parameters"].items():
            properties[name] = {
                "type": spec["type"],
                "description": spec.get("description", ""),
            }
            if spec.get("items"):
                properties[name]["items"] = spec["items"]
            if spec.get("enum"):
                properties[name]["enum"] = spec["enum"]
            if spec.get("required", False):
                required.append(name)

        tools.append(
            Tool(
                name=defn["name"],
                description=defn["description"],
                inputSchema={
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            )
        )
    return ListToolsResult(tools=tools)


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """Execute a HyperX tool."""
    try:
        tools = get_tools()

        # Map MCP tool names to SDK tool names
        tool_mapping = {
            "hyperx_search": "search",
            "hyperx_lookup": "lookup",
            "hyperx_paths": "paths",
            "hyperx_explorer": "explorer",
            "hyperx_explain": "explain",
            "hyperx_relationships": "relationships",
            "hyperx_entity_crud": "entity_crud",
            "hyperx_hyperedge_crud": "hyperedge_crud",
        }

        sdk_tool_name = tool_mapping.get(name)
        if not sdk_tool_name:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True,
            )

        # Execute the tool
        result = tools.execute(sdk_tool_name, **arguments)

        # Format response with quality signals
        response = {
            "success": result.success,
            "data": result.data,
            "quality": {
                "confidence": result.quality.confidence,
                "coverage": result.quality.coverage,
                "diversity": result.quality.diversity,
                "should_retrieve_more": result.quality.should_retrieve_more,
                "suggested_refinements": result.quality.suggested_refinements,
            } if result.quality else None,
        }

        if not result.success:
            response["error"] = result.error

        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(response, indent=2, default=str))],
            isError=not result.success,
        )

    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True,
        )


def create_server() -> Server:
    """Create and return the MCP server instance."""
    return server


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Main entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
