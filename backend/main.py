"""
FastAPI application for the Research Assistant API.

Provides REST endpoints for searching and analyzing academic papers.
"""

import json
import logging
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents import run_research_workflow
from schemas import ResearchResponse

# Load environment variables at startup
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# CACHING LAYER
# ============================================================

# Cache storage: {query: {"result": data, "timestamp": time}}
_cache: dict[str, dict] = {}

# Cache TTL: 1 hour (3600 seconds)
CACHE_TTL_SECONDS = 3600


def normalize_cache_key(query: str) -> str:
    """Normalize query string for cache key."""
    return query.strip().lower()


def cache_get(query: str) -> dict | None:
    """
    Get cached result if exists and not expired.

    Returns:
        Cached result dict or None if miss/expired
    """
    key = normalize_cache_key(query)

    if key not in _cache:
        return None

    entry = _cache[key]
    age = time.time() - entry["timestamp"]

    # Check if expired
    if age > CACHE_TTL_SECONDS:
        del _cache[key]
        return None

    return entry["result"]


def cache_set(query: str, result: dict) -> None:
    """Store result in cache with current timestamp."""
    key = normalize_cache_key(query)
    _cache[key] = {
        "result": result,
        "timestamp": time.time()
    }


def cache_stats() -> dict:
    """Get cache statistics."""
    now = time.time()
    valid_entries = sum(
        1 for entry in _cache.values()
        if now - entry["timestamp"] <= CACHE_TTL_SECONDS
    )
    return {
        "total_entries": len(_cache),
        "valid_entries": valid_entries,
        "ttl_seconds": CACHE_TTL_SECONDS
    }


# ============================================================
# FASTAPI APP
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    logger.info("Starting Research Assistant API...")
    yield
    logger.info("Shutting down Research Assistant API...")


# Initialize FastAPI app
app = FastAPI(
    title="Research Assistant API",
    description="Multi-Agent system for searching and analyzing academic papers from arXiv",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request model
class ResearchRequest(BaseModel):
    """Request body for the research endpoint."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The research topic to search for",
        json_schema_extra={"example": "retrieval augmented generation"}
    )


# Response model for errors
class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str
    error_type: str = "processing_error"


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Research Assistant API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "agents": ["Researcher", "Analyst"],
        "tools": ["search_arxiv"],
        "cache": cache_stats()
    }


@app.post(
    "/api/research",
    response_model=ResearchResponse,
    responses={
        200: {"description": "Successful research results"},
        500: {"model": ErrorResponse, "description": "Processing error"}
    }
)
async def research(request: ResearchRequest):
    """
    Search for academic papers and return analyzed results.

    This endpoint triggers the multi-agent workflow:
    1. Researcher agent searches arXiv for relevant papers
    2. Analyst agent summarizes and scores each paper
    3. Returns structured JSON with paper details

    Results are cached for 1 hour to improve performance.
    """
    query = request.query
    logger.info(f"Received research request for query: '{query}'")

    # Check cache first
    cached = cache_get(query)
    if cached:
        print("🚀 CACHE HIT")
        logger.info(f"Cache hit for query: '{query}'")
        return ResearchResponse(**cached)

    print("🐢 CACHE MISS")
    logger.info(f"Cache miss for query: '{query}' - running agent workflow")

    try:
        # Run the multi-agent workflow
        result = await run_research_workflow(query)

        # Parse the JSON result
        try:
            parsed_result = json.loads(result)
            response = ResearchResponse(**parsed_result)

            # Store in cache
            cache_set(query, parsed_result)

            logger.info(f"Successfully processed query: '{query}' - Found {response.total_results} papers")
            return response

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse agent response as JSON: {e}")
            logger.error(f"Raw response: {result[:500]}...")

            # Try to extract JSON from the response
            extracted = extract_json_from_text(result)
            if extracted:
                response = ResearchResponse(**extracted)
                # Store in cache
                cache_set(query, extracted)
                return response

            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse agent response as valid JSON: {str(e)}"
            )

        except Exception as e:
            logger.error(f"Failed to validate response against schema: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Response validation failed: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Research workflow failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Research workflow failed: {str(e)}"
        )


@app.delete("/api/cache")
async def clear_cache():
    """Clear all cached results."""
    global _cache
    count = len(_cache)
    _cache = {}
    logger.info(f"Cache cleared: {count} entries removed")
    return {"message": f"Cache cleared: {count} entries removed"}


def extract_json_from_text(text: str) -> dict | None:
    """
    Attempt to extract JSON from text that may contain additional content.
    """
    clean_text = text.strip()

    # Remove markdown code blocks
    if "```json" in clean_text:
        start = clean_text.find("```json") + 7
        end = clean_text.find("```", start)
        if end > start:
            clean_text = clean_text[start:end].strip()
    elif "```" in clean_text:
        start = clean_text.find("```") + 3
        end = clean_text.find("```", start)
        if end > start:
            clean_text = clean_text[start:end].strip()

    # Find JSON object boundaries
    start_idx = clean_text.find("{")
    end_idx = clean_text.rfind("}") + 1

    if start_idx != -1 and end_idx > start_idx:
        json_str = clean_text[start_idx:end_idx]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
