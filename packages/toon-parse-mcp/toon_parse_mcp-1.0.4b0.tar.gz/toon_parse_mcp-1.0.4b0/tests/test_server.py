import pytest
from src.toon_parse_mcp.server import optimize_input_context, get_protocol
import os

def test_optimize_input_context_json():
    raw_json = '[{"name": "test", "value": 123}, {"name": "test2", "value": 456}]'
    result = optimize_input_context(raw_json)
    assert "---OPTIMIZATION SUCCESSFUL---" in result
    # TOON format check for list/tabular
    assert "[2]{name,value}:" in result

def test_get_protocol():
    protocol = get_protocol()
    assert "# EFFICIENCY PROTOCOL" in protocol
    assert "read_and_optimize_file" in protocol

@pytest.mark.asyncio
async def test_read_and_optimize_file_missing(tmp_path):
    # Since we can't easily mock FastMCP tool calls directly without more setup,
    # we test the underlying logic if exposed, but server.py tools are sync.
    from src.toon_parse_mcp.server import read_and_optimize_file
    
    result = read_and_optimize_file("non_existent_file.txt")
    assert "Error: File not found" in result

def test_read_and_optimize_file_success(tmp_path):
    from src.toon_parse_mcp.server import read_and_optimize_file
    test_file = tmp_path / "test.py"
    test_file.write_text("def test():\n    # comment\n    pass")
    
    result = read_and_optimize_file(str(test_file))
    assert "---OPTIMIZATION SUCCESSFUL" in result
    assert "# comment" not in result
    assert "def test():" in result
