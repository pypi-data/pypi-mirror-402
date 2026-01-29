import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

from recursor.mcp.client import RecursorClient

# Initialize the MCP server
mcp = FastMCP("Recursor")

# Initialize API Client (lazy load to allow env vars to be set)
_client = None

def get_client() -> RecursorClient:
    global _client
    if not _client:
        _client = RecursorClient()
    return _client
