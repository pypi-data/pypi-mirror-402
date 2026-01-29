# Extent Report MCP Server

This is a Model Context Protocol (MCP) server that enables AI assistants (like Claude, Cursor, and QAFlow) to read, analyze, and understand Extent Reports.

## Features

- Parse Extent Reports (JSON and Spark HTML formats)
- Extract test summaries (Pass/Fail/Skip rates)
- Retrieve detailed failure analysis including stack traces
- Compare reports to identify regressions

## Installation

```bash
# Install with uv (recommended)
uv tool install mcp-extent

# Or install with pip
pip install mcp-extent
```

## Usage (Local Development)

Since you are running this from source, add the total path to your configuration:

```json
{
  "mcpServers": {
    "mcp-extent": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "D:/mcp-extent", 
        "mcp-extent"
      ]
    }
  }
}
```

> **Note:** Adjust the path `D:/mcp-extent` if you move the project.

## Tools

- `get_extent_report`: Parse full report
- `get_test_summary`: Get high-level stats
- `get_failed_tests`: Get detailed failure info
- `analyze_failures`: Pattern matching for failures
- `compare_reports`: Compare two report runs
