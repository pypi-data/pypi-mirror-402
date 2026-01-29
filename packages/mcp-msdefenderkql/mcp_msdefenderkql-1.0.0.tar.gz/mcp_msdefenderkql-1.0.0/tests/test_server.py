"""Tests for the MCP Defender Advanced Hunting server."""

import pytest

from mcp_defender.server import list_tools


@pytest.mark.asyncio
async def test_list_tools():
    """Test that only hunting tools are exposed."""
    tools = await list_tools()
    tool_names = [t.name for t in tools]

    # Should only have hunting-focused tools
    assert "run_hunting_query" in tool_names
    assert "get_hunting_schema" in tool_names

    # Should NOT have alerts/incidents (moved to streaming pipeline)
    assert "list_incidents" not in tool_names
    assert "get_incident" not in tool_names
    assert "list_alerts" not in tool_names

    # Should only be 2 tools
    assert len(tools) == 2


@pytest.mark.asyncio
async def test_run_hunting_query_tool_schema():
    """Test that run_hunting_query has correct input schema."""
    tools = await list_tools()
    query_tool = next(t for t in tools if t.name == "run_hunting_query")

    assert query_tool.inputSchema["required"] == ["query"]
    assert "query" in query_tool.inputSchema["properties"]


@pytest.mark.asyncio
async def test_get_hunting_schema_tool_schema():
    """Test that get_hunting_schema has correct input schema."""
    tools = await list_tools()
    schema_tool = next(t for t in tools if t.name == "get_hunting_schema")

    # table_name is optional
    assert schema_tool.inputSchema["required"] == []
    assert "table_name" in schema_tool.inputSchema["properties"]
