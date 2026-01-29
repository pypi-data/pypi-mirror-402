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
    max_results: int = 10,
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
    
    system_prompt = f"""You are a search assistant. Search the web and return results in THREE sections:

## Section 1: Summary
A brief overview (3-5 sentences) answering the query based on search results.

## Section 2: Search Results
List EXACTLY {max_results} results like Google/SearXNG:

1. **[Title]**
   [URL]
   Brief description (1-2 sentences)

2. **[Title]**
   [URL]
   Brief description

(continue for {max_results} results)

## Section 3: Sources
List all source citations with links.

RULES:
- Use the same language as the query
- Section 1 should be a concise summary
- Section 2 should look like search engine results
- Section 3 should list all referenced sources
"""
    
    payload = {
        "model": model,
        "max_tokens": 64000,
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
            description="""[Web Search Tool] Search the internet for real-time information and return a list of links.

## When to Use
- User asks about people, companies, or products you don't know
- User asks about latest news, events, or developments  
- User asks about events after 2024
- User explicitly requests a search
- You are uncertain if your answer is accurate

⚠️ Do NOT say "I cannot access latest information" - USE this tool to search!

## Parameters
- query (required): Search keywords. Use the same language as the user's question.
- max_results (optional): Number of results. Use 3-5 for simple questions, 10+ for complex ones.
- model (optional): Search model. Default gemini-3-flash, use gemini-3-pro-high for higher quality.

## Examples
1. Simple: mcp_search(query="Who is Kanru Hua")
2. Detailed: mcp_search(query="Synthesizer V latest version", max_results=10)
3. High quality: mcp_search(query="AI singing synthesis", model="gemini-3-pro-high", max_results=10)

## Return Format
Returns list of Title + URL + Summary. Use webfetch to get full content of interesting links.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keywords. Use user's language for better results."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results. 3-5 for simple, 10+ for complex. Default 8",
                        "default": 8
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
