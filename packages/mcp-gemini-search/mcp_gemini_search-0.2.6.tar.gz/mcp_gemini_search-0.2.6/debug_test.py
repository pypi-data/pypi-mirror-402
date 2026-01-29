"""
Debug test - Show full API response
"""

import asyncio
import httpx
import json
import os

ANTIGRAVITY_URL = os.environ.get("MCP_SEARCH_URL", "http://localhost:8045/v1/messages")
ANTIGRAVITY_API_KEY = os.environ.get(
    "MCP_SEARCH_API_KEY", "sk-a7903547f2ec4b44b766edd786765223"
)


async def test_raw_response():
    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTIGRAVITY_API_KEY,
        "anthropic-version": "2023-06-01",
        "x-enable-grounding": "true",
        "x-google-search": "true",
    }

    payload = {
        "model": "gemini-3-flash",
        "max_tokens": 8000,
        "system": "You are a search assistant. Search the web and provide results with source URLs.",
        "messages": [{"role": "user", "content": "2025年中日风波最新进展"}],
        "metadata": {"grounding": True, "google_search": True},
        "stream": False,
    }

    print("=" * 70)
    print("Testing raw Anthropic format response")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(ANTIGRAVITY_URL, headers=headers, json=payload)

        print(f"Status: {response.status_code}")
        print("-" * 70)

        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()

        # Check for grounding-related fields
        print("=" * 70)
        print("Checking for grounding metadata fields:")
        print("=" * 70)
        for key in result.keys():
            print(f"  - {key}")
            if key == "content":
                for i, block in enumerate(result["content"]):
                    print(f"    [{i}] type: {block.get('type')}")
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        # Check if text contains grounding URLs
                        if "vertexaisearch" in text or "grounding" in text.lower():
                            print(f"        Contains grounding references!")


if __name__ == "__main__":
    asyncio.run(test_raw_response())
