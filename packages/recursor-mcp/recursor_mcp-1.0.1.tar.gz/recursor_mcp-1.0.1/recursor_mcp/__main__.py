"""
Entry point for running MCP server or HTTP bridge
"""
import os
import sys


def main():
    """Main entry point - choose between MCP server and HTTP bridge"""
    
    # Check if HTTP bridge mode is requested
    if "--http" in sys.argv or os.getenv("MCP_MODE") == "http":
        print("🌐 Starting MCP HTTP Bridge...")
        from recursor.mcp.http_bridge import main as http_main
        http_main()
    else:
        print("🔌 Starting MCP Server (stdio mode)...")
        from recursor.mcp.server import main as mcp_main
        mcp_main()

if __name__ == "__main__":
    main()
