# MCP Search Server

A Model Context Protocol (MCP) server that provides web search capabilities for AI assistants using Gemini models.

## Features

- 🔍 Web search via Gemini's grounding API
- 📝 Three-section output: Summary + Search Results + Sources
- 🚀 Works with OpenCode, Zed, Claude Desktop, and any MCP-compatible tool
- ⚡ Result caching for faster repeated queries
- 🌐 Language-adaptive (responds in user's query language)

## Installation

```bash
pip install mcp-search-server
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MCP_SEARCH_URL` | ⚠️ Yes | `http://localhost:8046/v1/messages` | Anthropic-compatible API endpoint |
| `MCP_SEARCH_API_KEY` | ⚠️ Yes | - | API key for the endpoint |
| `MCP_SEARCH_MODEL` | No | `gemini-3-flash` | Default search model |
| `MCP_SEARCH_CACHE_TTL` | No | `300` | Cache TTL in seconds |

### OpenCode Configuration

Add to your `opencode.json`:

```json
{
  "mcp": {
    "mcp-search": {
      "type": "local",
      "command": ["python", "-m", "mcp_search"],
      "env": {
        "MCP_SEARCH_URL": "http://localhost:8046/v1/messages",
        "MCP_SEARCH_API_KEY": "sk-your-api-key"
      }
    }
  }
}
```

### Zed Configuration

Add to your `settings.json`:

```json
{
  "language_models": {
    "mcp": {
      "mcp-search": {
        "command": ["python", "-m", "mcp_search"],
        "env": {
          "MCP_SEARCH_URL": "http://localhost:8046/v1/messages",
          "MCP_SEARCH_API_KEY": "sk-your-api-key"
        }
      }
    }
  }
}
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-search": {
      "command": "python",
      "args": ["-m", "mcp_search"],
      "env": {
        "MCP_SEARCH_URL": "http://localhost:8046/v1/messages",
        "MCP_SEARCH_API_KEY": "sk-your-api-key"
      }
    }
  }
}
```

## Usage

Once configured, the AI assistant can use the `mcp_search` tool:

```
mcp_search(query="Who is Kanru Hua", max_results=5)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | ✅ | Search keywords |
| `max_results` | integer | No | Number of results (default: 8) |
| `model` | string | No | Search model to use |

## Output Format

The search returns three sections:

1. **Summary**: Brief overview answering the query
2. **Search Results**: Numbered list of results with title, URL, and description
3. **Sources**: Complete list of source citations

## License

MIT
