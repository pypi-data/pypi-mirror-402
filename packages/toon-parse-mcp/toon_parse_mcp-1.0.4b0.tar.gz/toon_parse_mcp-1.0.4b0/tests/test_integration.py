import pytest
import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Get the path to the current python interpreter (should be in toon-parse-env)
PYTHON_EXE = sys.executable

@pytest.mark.asyncio
async def test_server_stdio_integration():
    """
    Spawns the server as a subprocess and verifies it can be communicated with over stdio.
    """
    server_params = StdioServerParameters(
        command=PYTHON_EXE,
        args=["-m", "src.toon_parse_mcp.server"],
        env=os.environ.copy()
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. Initialize
            await session.initialize()

            # 2. List tools
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            assert "optimize_input_context" in tool_names
            assert "read_and_optimize_file" in tool_names

            # 3. Call optimize_input_context
            result = await session.call_tool(
                "optimize_input_context",
                arguments={"raw_input": '{"test": 123}'}
            )
            assert not result.isError
            content = result.content[0].text
            assert "---OPTIMIZATION SUCCESSFUL---" in content
            assert "test: 123" in content

            # 4. Call get_resource (via list and read)
            resources = await session.list_resources()
            resource_uris = [str(r.uri) for r in resources.resources]
            assert "protocol://mandatory-efficiency" in resource_uris

            res_content = await session.read_resource("protocol://mandatory-efficiency")
            assert "# EFFICIENCY PROTOCOL" in res_content.contents[0].text
