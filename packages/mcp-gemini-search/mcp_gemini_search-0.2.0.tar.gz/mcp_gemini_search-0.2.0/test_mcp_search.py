"""
Test script for MCP Search Server
Tests the do_search function directly without MCP protocol
"""
import asyncio
import sys
sys.path.insert(0, "d:/Project/llm/mcp-search-server/src")

from mcp_search.server import do_search, parse_search_results

async def test_search():
    print("=" * 70)
    print("Test 1: Basic search with gemini-3-flash")
    print("=" * 70)
    
    result = await do_search(
        query="2025年中日风波最新进展",
        max_results=10,
        model="gemini-3-flash"
    )
    
    print(f"Result length: {len(result)} characters")
    print("-" * 70)
    print(result[:2000])  # First 2000 chars
    print("..." if len(result) > 2000 else "")
    print()
    
    # Test cache
    print("=" * 70)
    print("Test 2: Cache test (same query should be cached)")
    print("=" * 70)
    
    import time
    start = time.time()
    result2 = await do_search(
        query="2025年中日风波最新进展",
        max_results=5,
        model="gemini-3-flash"
    )
    elapsed = time.time() - start
    
    is_cached = "[Cached Result]" in result2
    print(f"Cached: {is_cached}")
    print(f"Time: {elapsed:.3f}s")
    print()
    
    # Test with gemini-3-pro-high
    print("=" * 70)
    print("Test 3: Search with gemini-3-pro-high (higher quality)")
    print("=" * 70)
    
    result3 = await do_search(
        query="Synthesizer V AI singing synthesis",
        max_results=3,
        model="gemini-3-pro-high"
    )
    
    print(f"Result length: {len(result3)} characters")
    print("-" * 70)
    print(result3[:1500])
    print("..." if len(result3) > 1500 else "")
    print()
    
    # Parse results
    print("=" * 70)
    print("Test 4: Parse search results (extract URLs)")
    print("=" * 70)
    
    parsed = parse_search_results(result)
    print(f"Found {len(parsed)} parsed links:")
    for i, link in enumerate(parsed[:5], 1):
        print(f"  {i}. {link.get('source', 'Unknown')}: {link.get('url', '')[:60]}...")


if __name__ == "__main__":
    asyncio.run(test_search())
