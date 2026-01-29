"""
MCP Search Server - Web Search Proxy Service
Returns structured search results list for the main model to decide whether to fetch content.
"""

import asyncio
import json
import hashlib
import time
import re
import os
from typing import Optional
from datetime import datetime

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)

# Configuration (read from environment variables with defaults)
ANTIGRAVITY_URL = os.environ.get("MCP_SEARCH_URL", "http://localhost:8045/v1/messages")
ANTIGRAVITY_API_KEY = os.environ.get("MCP_SEARCH_API_KEY", "sk-1234567890")
DEFAULT_MODEL = os.environ.get("MCP_SEARCH_MODEL", "gemini-3-flash")
CACHE_TTL_SECONDS = int(os.environ.get("MCP_SEARCH_CACHE_TTL", "300"))

# Simple in-memory cache
_cache: dict[str, tuple[float, str]] = {}


def _get_cache_key(query: str, model: str, max_results: int) -> str:
    """Generate cache key"""
    return hashlib.md5(f"{query}:{model}:{max_results}".encode()).hexdigest()


def _get_from_cache(key: str) -> Optional[str]:
    """Get result from cache"""
    if key in _cache:
        timestamp, result = _cache[key]
        if time.time() - timestamp < CACHE_TTL_SECONDS:
            return result
        else:
            del _cache[key]
    return None


def _set_cache(key: str, result: str):
    """Set cache"""
    _cache[key] = (time.time(), result)


def parse_search_results(text: str) -> list[dict]:
    """Parse links from search model response"""
    results = []
    
    # Extract grounding-api-redirect links
    urls = re.findall(r'https://vertexaisearch\.cloud\.google\.com/grounding-api-redirect/[^\s\)]+', text)
    
    # Extract domain info
    domains = re.findall(r'\[([^\]]+)\]\((https://[^\)]+)\)', text)
    
    for domain, url in domains:
        results.append({
            "source": domain,
            "url": url
        })
    
    return results


async def do_search(
    query: str,
    max_results: int = 15,
    model: str = DEFAULT_MODEL,
) -> str:
    """Execute search request and return structured link list"""
    
    # Check cache
    cache_key = _get_cache_key(query, model, max_results)
    cached = _get_from_cache(cache_key)
    if cached:
        return f"[Cached Result]\n{cached}"
    
    # Build request
    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTIGRAVITY_API_KEY,
        "anthropic-version": "2023-06-01"
    }
    
    system_prompt = f"""Search the web for: "{query}"

CRITICAL: You MUST return AT LEAST {max_results} different search results.

For EACH result, include:
- Title
- URL
- Brief excerpt or key facts

If the initial search returns fewer than {max_results} results, try related keywords to find more.
List ALL results found, do NOT filter or summarize them.
"""
    
    payload = {
        "model": model,
        "max_tokens": 200000,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": f"Search: {query}"
            }
        ],
        "tools": [
            {
                "name": "web_search",
                "description": "Web search",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        ],
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(ANTIGRAVITY_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            return f"Search failed: {response.status_code} - {response.text[:200]}"
        
        result = response.json()
        
        # Extract text content
        texts = []
        for block in result.get("content", []):
            if block.get("type") == "text":
                texts.append(block.get("text", ""))
        
        full_result = "\n".join(texts)
        
        # Cache result
        _set_cache(cache_key, full_result)
        
        return full_result


# Create MCP server
server = Server("mcp-search-server")


@server.list_tools()
async def list_tools():
    """List available tools"""
    return [
        Tool(
            name="mcp_search",
            description="""[Web Search] Search the internet for real-time information.

## When to Use
- User asks about current events, news, or recent developments
- User explicitly requests a search or latest information
- Topics after your knowledge cutoff date
- You need to verify uncertain facts

## When NOT to Use
- User asks general knowledge questions you can answer confidently
- Historical facts or stable information
- Following up on previous search results (use the data you already have)
- Simple coding questions or documentation lookups

## Tips
- Returns RAW search data - you process and summarize it yourself
- You CAN search multiple times with different queries for comprehensive results
- Use specific keywords in the user's language
- Start with fewer results (5-10), increase if needed

## Parameters
- query (required): Search keywords
- max_results (optional): Default 15. Use 5-10 for simple, 20+ for research tasks
- model (optional): gemini-3-flash (default, fast) or gemini-3-pro-high (quality)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keywords. Use user's language for better results."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results. 5-10 for simple, 20+ for research. Default 15",
                        "default": 15
                    },
                    "model": {
                        "type": "string",
                        "description": "Search model ID. Recommended: gemini-3-flash (fast), gemini-3-pro-high (quality). Leave empty to use server default."
                    }
                },
                "required": ["query"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls"""
    if name == "mcp_search":
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 10)
        model = arguments.get("model", DEFAULT_MODEL)
        
        result = await do_search(
            query=query,
            max_results=max_results,
            model=model
        )
        
        return [TextContent(type="text", text=result)]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Start server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
