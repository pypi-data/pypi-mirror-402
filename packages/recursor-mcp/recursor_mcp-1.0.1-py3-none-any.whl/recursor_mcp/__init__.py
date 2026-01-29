"""
Entry point for running the MCP server.
"""

import asyncio

import recursor.mcp.resources

# Import tools and resources to register them
import recursor.mcp.tools
from recursor.mcp.server import mcp


def main():
    """Run the MCP server using stdio transport"""
    mcp.run()

if __name__ == "__main__":
    main()
