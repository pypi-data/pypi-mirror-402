"""
HTTP Bridge for MCP Server
Exposes MCP tools as REST API endpoints for Docker, n8n, and IDE integration
"""
import os
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from recursor.infrastructure.monitoring import get_logger
from recursor.mcp.client import RecursorClient

logger = get_logger("mcp_http_bridge")


# Pydantic models for request/response
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query for corrections")
    limit: int = Field(default=5, ge=1, le=50, description="Maximum number of results")


class SearchResponse(BaseModel):
    results: list
    count: int


class CorrectionRequest(BaseModel):
    original_code: str = Field(..., description="Original incorrect code")
    fixed_code: str = Field(..., description="Corrected code")
    explanation: str = Field(..., description="Explanation of the correction")


class CorrectionResponse(BaseModel):
    success: bool
    message: str
    correction_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    mcp_server: str
    api_connection: str


# Initialize FastAPI app
app = FastAPI(
    title="Recursor MCP HTTP Bridge",
    description="HTTP wrapper for Recursor MCP tools - enables Docker, n8n, and IDE integration",
    version="1.0.0"
)

# Add CORS middleware with secure configuration
# Get allowed origins from environment or use secure defaults
allowed_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)


# Dependency to verify API key
async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify the API key from request headers"""
    expected_key = os.getenv("RECURSOR_API_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: RECURSOR_API_KEY not set"
        )
    
    if x_api_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return x_api_key


# Initialize client
def get_client():
    """Get RecursorClient instance"""
    try:
        return RecursorClient()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "mcp_server": "http_bridge",
        "api_connection": "ready"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    client = get_client()
    
    try:
        # Test API connection
        await client.check_health()
        api_status = "connected"
    except Exception as e:
        api_status = f"error: {str(e)}"
    
    return {
        "status": "online",
        "mcp_server": "http_bridge",
        "api_connection": api_status
    }


@app.post("/tools/search", response_model=SearchResponse)
async def search_memory(
    request: SearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Search Recursor's memory for relevant corrections
    
    This endpoint wraps the MCP `search_memory` tool, allowing you to search
    for past corrections and coding patterns.
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8001/tools/search" \\
      -H "X-API-Key: your_api_key" \\
      -H "Content-Type: application/json" \\
      -d '{"query": "authentication", "limit": 5}'
    ```
    """
    client = get_client()
    
    try:
        results = await client.search_corrections(request.query, request.limit)
        return {
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/tools/correct", response_model=CorrectionResponse)
async def add_correction(
    request: CorrectionRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Add a new correction to Recursor's memory
    
    This endpoint wraps the MCP `add_correction` tool, allowing you to save
    corrections that will be remembered for future reference.
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8001/tools/correct" \\
      -H "X-API-Key: your_api_key" \\
      -H "Content-Type: application/json" \\
      -d '{
        "original_code": "password = request.form[\\"password\\"]",
        "fixed_code": "password_hash = hash_password(request.form[\\"password\\"])",
        "explanation": "Always hash passwords before storing"
      }'
    ```
    """
    client = get_client()
    
    try:
        result = await client.add_correction(
            request.original_code,
            request.fixed_code,
            request.explanation
        )
        
        return {
            "success": True,
            "message": "Correction saved successfully",
            "correction_id": result.get("id")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save correction: {str(e)}")


@app.get("/tools/recent", response_model=SearchResponse)
async def get_recent_activity(
    limit: int = 10,
    api_key: str = Depends(verify_api_key)
):
    """
    Get recent corrections and activity
    
    This endpoint wraps the MCP `recursor://recent_activity` resource.
    
    **Example:**
    ```bash
    curl "http://localhost:8001/tools/recent?limit=10" \\
      -H "X-API-Key: your_api_key"
    ```
    """
    client = get_client()
    
    try:
        # Use search with empty query to get recent items
        results = await client.search_corrections("", limit)
        return {
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent activity: {str(e)}")


def main():
    """Run the HTTP bridge server"""
    port = int(os.getenv("MCP_HTTP_PORT", "8001"))
    host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
    
    logger.info(f"🚀 Starting Recursor MCP HTTP Bridge on {host}:{port}")
    logger.info(f"📚 API Documentation: http://{host}:{port}/docs")
    # API key status (no preview for security)
    api_key_status = "CONFIGURED" if os.getenv('RECURSOR_API_KEY') else "NOT SET"
    logger.info(f"🔑 API Key: {api_key_status}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
