# Dataloop MCP Proxy Server

This is the main proxy for the Dataloop Micro MCPs, installable as a Python package.

## Installation

```shell
pip install git+<repository-url>
```

## Usage

You can run the proxy server via CLI:

```shell
# Basic usage
dtlpymcp start

# With custom sources file
dtlpymcp start --sources-file /path/to/sources.json

# With custom initialization timeout (default: 30 seconds)
dtlpymcp start --init-timeout 60.0
```

Or using Python module syntax:

```shell
python -m dtlpymcp start
```

## Local Development

- Requires Python 3.10+
- Install dependencies with `pip install -e .`
- Run tests with `pytest`

## Architecture

The server uses a modular architecture with utilities for safe async initialization:

- `dtlpymcp/proxy.py` - Main server implementation using FastMCP
- `dtlpymcp/utils/server_utils.py` - Safe async initialization utilities
- `dtlpymcp/utils/dtlpy_context.py` - Dataloop context management

## Cursor MCP Integration

To add this MCP to Cursor, add the following to your configuration:

### Docker Example
```json
{
  "mcpServers": {
    "dataloop-ai-mcp": {
      "command": "docker run -i --rm -e DATALOOP_API_KEY docker.io/dataloopai/mcp:latest",
      "env": {
        "DATALOOP_API_KEY": "API KEY"
      }
    }
  }
}
```

### Local CLI Example
```json
{
  "mcpServers": {
    "dataloop-ai-mcp": {
      "command": "uvx",
      "args": ["dtlpymcp", "start"],
      "env": {
        "DATALOOP_ENV": "prod",
        "DATALOOP_API_KEY": "API KEY"
      }
    }
  }
}
```

Replace `API KEY` with your actual Dataloop API key.