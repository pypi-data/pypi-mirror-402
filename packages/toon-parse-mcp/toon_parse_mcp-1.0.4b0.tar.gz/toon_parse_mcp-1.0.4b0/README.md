# toon-parse MCP Server

mcp-name: io.github.ankitpal181/toon-parse-mcp

[![MCP Registry](https://img.shields.io/badge/MCP-Registry-blue)](https://registry.modelcontextprotocol.io/)
[![PyPI version](https://badge.fury.io/py/toon-parse-mcp.svg)](https://badge.fury.io/py/toon-parse-mcp)

A specialized [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that optimizes token usage by converting data to TOON (Token-Oriented Object Notation) and stripping non-essential context from code files.

## Overview

The `toon-parse-mcp` MCP server helps AI agents (like Cursor, Claude Desktop, etc.) operate more efficiently by:
1.  **Optimizing Code Context**: Stripping comments and redundant spacing from code files while preserving functional structure and docstrings.
2.  **Data Format Conversion**: Converting JSON, XML, YAML, and CSV inputs into the compact TOON format to save tokens.
3.  **Mandatory Efficiency Protocol**: A built-in resource that instructs LLMs to prioritize token-saving tools.

## Features

### Tools
- `optimize_input_context(raw_input: str)`: Processes raw text data (JSON/XML/CSV/YAML) and returns optimized TOON format.
- `read_and_optimize_file(file_path: str)`: Reads a local code file and returns a token-optimized version (no inline comments, minimized whitespace).

### Resources
- `protocol://mandatory-efficiency`: Provides a strict system instruction prompt for LLMs to ensure they use the optimization tools correctly.

## Installation

```bash
pip install toon-parse-mcp
```

## Configuration

### Cursor

1. Open Cursor Settings -> MCP.
2. Click "+ Add New MCP Server".
3. Name: `toon-parse-mcp`
4. Type: `command`
5. Command: `python3 -m toon_parse_mcp.server` (Ensure your environment is active or use absolute path to python)

### Windsurf

1. Click the hammer icon in the Cascade toolbar and select "Configure".
2. Alternatively, edit `~/.codeium/windsurf/mcp_config.json` directly.
3. Add the following to the `mcpServers` object:

```json
{
  "mcpServers": {
    "toon-parse-mcp": {
      "command": "python3",
      "args": ["-m", "toon_parse_mcp.server"]
    }
  }
}
```

### Antigravity

1. Open the MCP store via the "..." menu at the top right of the agent panel.
2. Select "Manage MCP Servers" -> "View raw config".
3. Alternatively, edit `~/.gemini/antigravity/mcp_config.json` directly.
4. Add the following to the `mcpServers` object:

```json
{
  "mcpServers": {
    "toon-parse-mcp": {
      "command": "python3",
      "args": ["-m", "toon_parse_mcp.server"]
    }
  }
}
```

### Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "toon-parse-mcp": {
      "command": "python3",
      "args": ["-m", "toon_parse_mcp.server"]
    }
  }
}
```

## Usage

When the server is active, the AI will have access to the `optimize_input_context` and `read_and_optimize_file` tools. You can also refer to the efficiency protocol by asking the AI to "check the mandatory efficiency protocol".

## Testing

To run the test suite:

1. Install test dependencies:
   ```bash
   pip install -e ".[test]"
   ```
2. Run tests:
   ```bash
   pytest tests/
   ```

## Requirements

- Python >= 3.10
- `mcp` >= 1.25.0
- `toon-parse` >= 2.4.3

## License

MIT License - see [LICENSE](LICENSE) for details.
