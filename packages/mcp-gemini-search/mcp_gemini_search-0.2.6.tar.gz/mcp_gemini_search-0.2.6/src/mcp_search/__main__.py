"""
MCP Search Server - Entry point for python -m mcp_search
"""

from .server import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
