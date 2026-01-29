"""
HTTP Client for Recursor MCP Server.
Handles authentication and communication with the Recursor API.
"""

import os
from typing import Any, Dict, List, Optional

import aiohttp


class RecursorClient:
    def __init__(self):
        self.api_url = os.getenv("RECURSOR_API_URL", "https://recursor.dev/v1")
        self.api_key = os.getenv("RECURSOR_API_KEY")
        
        if not self.api_key:
            raise ValueError("RECURSOR_API_KEY environment variable is required")
            
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
    async def search_corrections(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search corrections via API"""
        async with aiohttp.ClientSession() as session:
            params = {"query": query, "limit": limit}
            async with session.get(f"{self.api_url}/client/corrections/search", headers=self.headers, params=params) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"Error searching corrections: {resp.status} - {error_text}")
                    return []
                
                data = await resp.json()
                return data.get("corrections", [])

    async def add_correction(self, input_text: str, output_text: str, explanation: str) -> Dict[str, Any]:
        """Add a correction via API"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "input_text": input_text,
                "output_text": output_text,
                "expected_output": output_text,
                "correction_type": "mcp_learned",
                "context": {"explanation": explanation, "source": "mcp"}
            }
            async with session.post(f"{self.api_url}/client/corrections/", headers=self.headers, json=payload) as resp:
                if resp.status != 201:
                    error_text = await resp.text()
                    raise Exception(f"Failed to add correction: {resp.status} - {error_text}")
                
                return await resp.json()

    async def check_health(self) -> bool:
        """Check if API is reachable"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/status/health") as resp:
                    return resp.status == 200
        except Exception:
            return False
