"""
MCP Search Server - Web Search Proxy for AI Assistants
"""

__version__ = "0.2.6"
__author__ = "cubase"

from .server import main, do_search

__all__ = ["main", "do_search"]
