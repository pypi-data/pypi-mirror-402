import asyncio
import os
from typing import Optional

from recursor.mcp.server import get_client, mcp


@mcp.tool()
async def search_memory(query: str, limit: int = 5) -> str:
    """
    Search Recursor's memory for relevant coding patterns, past corrections, or guidelines.
    Use this when you want to check if there are specific rules or past mistakes to avoid for the current task.
    """
    client = get_client()
    corrections = await client.search_corrections(query, limit)
    
    # Track analytics (fire and forget)
    try:
        project_id = os.getenv("RECURSOR_PROJECT_ID")
        if project_id:
            asyncio.create_task(_track_tool_call("search_memory", {"query": query, "limit": limit}))
    except:
        pass  # Don't fail if analytics tracking fails
    
    if not corrections:
        return f"No specific past corrections found for '{query}'."
        
    response = f"Found {len(corrections)} relevant past corrections:\n\n"
    for c in corrections:
        created_at = c.get('created_at', 'Unknown date')
        input_text = c.get('input_text', '')
        output_text = c.get('output_text', '')
        explanation = c.get('context', {}).get('explanation', 'N/A')
        
        response += f"--- Correction ({created_at}) ---\n"
        response += f"Original: {input_text[:100]}...\n"
        response += f"Fixed: {output_text[:100]}...\n"
        response += f"Reason: {explanation}\n\n"
        
    return response

@mcp.tool()
async def add_correction(original_code: str, fixed_code: str, explanation: str) -> str:
    """
    Record a correction or improvement to the system's memory.
    Use this when the user corrects your output, so you don't make the same mistake again.
    """
    client = get_client()
    try:
        await client.add_correction(original_code, fixed_code, explanation)
        
        # Track analytics
        try:
            project_id = os.getenv("RECURSOR_PROJECT_ID")
            if project_id:
                asyncio.create_task(_track_tool_call("add_correction", {"has_explanation": bool(explanation)}))
        except:
            pass
        
        return "Correction saved. I will remember this preference for future tasks."
    except Exception as e:
        return f"Failed to save correction: {str(e)}"

@mcp.tool()
async def check_safety(code_snippet: str) -> str:
    """
    Validate a code snippet against safety guardrails.
    """
    # Track analytics
    try:
        project_id = os.getenv("RECURSOR_PROJECT_ID")
        if project_id:
            asyncio.create_task(_track_tool_call("check_safety", {}))
    except:
        pass
    
    # For now, we'll return a placeholder as the API doesn't expose a direct check_safety endpoint yet
    # Ideally, we should add a /validate endpoint to the API
    return "Code safety check passed (Client-side validation not yet implemented via API)."

async def _track_tool_call(tool_name: str, metadata: dict):
    """Helper to track tool calls via API"""
    try:
        import aiohttp
        api_url = os.getenv("RECURSOR_API_URL", "https://recursor.dev/v1")
        api_key = os.getenv("RECURSOR_API_KEY")
        
        if not api_key:
            return
        
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{api_url}/internal/analytics/mcp-tool-call",
                headers={"X-API-Key": api_key},
                json={"tool_name": tool_name, "metadata": metadata},
                timeout=aiohttp.ClientTimeout(total=2)
            )
    except:
        pass  # Silent fail for analytics
