"""
MCP Search Server - Web Search Proxy Service
Uses Antigravity proxy with OpenAI format to call Gemini with Google Search.
"""

import asyncio
import json
import hashlib
import time
import os
from typing import Optional

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configuration
ANTIGRAVITY_URL = os.environ.get(
    "MCP_SEARCH_URL", "http://localhost:8045/v1/chat/completions"
)
ANTIGRAVITY_API_KEY = os.environ.get("MCP_SEARCH_API_KEY", "sk-1234567890")
DEFAULT_MODEL = os.environ.get("MCP_SEARCH_MODEL", "gemini-3-flash")
CACHE_TTL_SECONDS = int(os.environ.get("MCP_SEARCH_CACHE_TTL", "300"))

# Simple in-memory cache
_cache: dict[str, tuple[float, str]] = {}


def _get_cache_key(query: str, model: str) -> str:
    return hashlib.md5(f"{query}:{model}".encode()).hexdigest()


def _get_from_cache(key: str) -> Optional[str]:
    if key in _cache:
        timestamp, result = _cache[key]
        if time.time() - timestamp < CACHE_TTL_SECONDS:
            return result
        del _cache[key]
    return None


def _set_cache(key: str, result: str):
    _cache[key] = (time.time(), result)


async def do_search(query: str, model: str = DEFAULT_MODEL) -> str:
    """Execute search using OpenAI format with google_search tool."""

    cache_key = _get_cache_key(query, model)
    if cached := _get_from_cache(cache_key):
        return f"[Cached]\n{cached}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ANTIGRAVITY_API_KEY}",
    }

    # OpenAI format with google_search function tool
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a search assistant. Search the web and provide comprehensive, factual results.",
            },
            {"role": "user", "content": query},
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "google_search",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ],
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(ANTIGRAVITY_URL, headers=headers, json=payload)

        if response.status_code != 200:
            return f"Search failed: {response.status_code} - {response.text[:300]}"

        result = response.json()

        # Extract content from OpenAI format
        choices = result.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")

            if content:
                _set_cache(cache_key, content)
                return content

        return f"No content: {json.dumps(result, ensure_ascii=False)[:500]}"


# MCP Server
server = Server("mcp-search-server")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="search_web",
            description="Performs a web search for a given query. Returns a summary of relevant information along with URL citations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "domain": {
                        "type": "string",
                        "description": "Optional domain to recommend the search prioritize",
                    },
                },
                "required": ["query"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_web":
        query = arguments.get("query", "")
        model = arguments.get("model", DEFAULT_MODEL)
        result = await do_search(query=query, model=model)
        return [TextContent(type="text", text=result)]
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
