"""
Test script for MCP Search Server
Tests the do_search function directly without MCP protocol
"""

import asyncio
import sys

sys.path.insert(0, "d:/Project/llm/mcp-search-server/src")

from mcp_search.server import do_search


async def test_search():
    print("=" * 70)
    print("Test 1: Basic search with gemini-3-flash")
    print("=" * 70)

    result = await do_search(
        query="Search: 反田葉月 Hatsuki Tanda D4DJ Bang Dream 地下偶像 2014-2026 经历"
    )

    print(f"Result length: {len(result)} characters")
    print("-" * 70)
    print(result[:2000])
    print("..." if len(result) > 2000 else "")
    print()

    # Test cache
    print("=" * 70)
    print("Test 2: Cache test (same query)")
    print("=" * 70)

    import time

    result3 = await do_search(
        query="Search: 反田葉月 Hatsuki Tanda D4DJ Bang Dream 地下偶像 2014-2026 经历",
        model="gemini-3-pro-high",
    )

    print(f"Result length: {len(result3)} characters")
    print("-" * 70)
    print(result3[:1500])
    print("..." if len(result3) > 1500 else "")


if __name__ == "__main__":
    asyncio.run(test_search())
