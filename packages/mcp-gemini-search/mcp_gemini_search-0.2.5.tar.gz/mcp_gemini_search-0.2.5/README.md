# MCP Search Server

A Model Context Protocol (MCP) server that provides web search capabilities via Gemini's grounding API.

## Features

- 🔍 Real-time web search powered by Google Gemini
- ⚡ Built-in caching (5 min TTL)
- 🎯 Structured search results (Title + URL + Summary)
- 🌍 Multi-language support

## Installation

```bash
pip install mcp-search-server
```

## Configuration

Set environment variables:

```bash
export MCP_SEARCH_URL="http://localhost:8045/v1/messages"
export MCP_SEARCH_API_KEY="your-api-key"
export MCP_SEARCH_MODEL="gemini-3-flash"  # or gemini-3-pro-high
export MCP_SEARCH_CACHE_TTL="300"  # seconds
```

## Usage

### As MCP Server (with Zed, Claude Desktop, etc.)

```json
{
  "mcpServers": {
    "mcp-search": {
      "command": "python",
      "args": ["-m", "mcp_search"],
      "env": {
        "MCP_SEARCH_URL": "http://localhost:8045/v1/messages",
        "MCP_SEARCH_API_KEY": "your-api-key",
        "MCP_SEARCH_MODEL": "gemini-3-flash"
      }
    }
  }
}
```

### As Python Library

```python
import asyncio
from mcp_search import do_search

result = asyncio.run(do_search(
    query="latest AI news",
    max_results=5,
    model="gemini-3-flash"
))
print(result)
```

## Tool Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | ✅ | Search keywords |
| `max_results` | integer | ❌ | Number of results (default: 8) |
| `model` | string | ❌ | Model ID (default: gemini-3-flash) |

## Requirements

- Python 3.10+
- [Antigravity Manager](https://github.com/lbjlaq/Antigravity-Manager) running locally

## License

MIT
