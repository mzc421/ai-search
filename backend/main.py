import logging
import time
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from services.search_service import SearchService
from services.security import detect_prompt_injection, sanitize_query
from core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Search Engine")


@app.middleware("http")
async def access_log_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"[HTTP] {request.method} {request.url.path} "
        f"status={response.status_code} duration={duration:.3f}s"
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

search_service = SearchService()


def _check_injection(query: str):
    if not settings.enable_injection_detection:
        return
    is_injection, confidence, reason = detect_prompt_injection(query)
    if is_injection and confidence >= settings.injection_block_threshold:
        logger.warning(
            f"[SECURITY] Blocked request due to injection detection "
            f"(confidence={confidence:.2f}). Reason: {reason}"
        )
        raise HTTPException(
            status_code=422,
            detail="内容包含不安全模式，请重新输入正常搜索内容"
        )


class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    score: Optional[float] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None


class SearchResponse(BaseModel):
    answer: str
    sources: List[SearchResult]
    related_questions: List[str]
    cache_hit: bool = False
    images: Optional[List[SearchResult]] = None
    video_results: Optional[List[SearchResult]] = None


@app.get("/")
async def root():
    return {"message": "AI Search Engine API"}


@app.post("/search")
@limiter.limit(f"{settings.rate_limit_search_per_minute}/minute")
async def search(request: Request, query: SearchQuery):
    _check_injection(query.query)
    return await search_service.search(query.query)


@app.post("/search/stream")
@limiter.limit(f"{settings.rate_limit_search_per_minute}/minute")
async def search_stream_post(request: Request, query: SearchQuery):
    _check_injection(query.query)
    return StreamingResponse(
        search_service.search_stream(query.query),
        media_type="text/event-stream"
    )


@app.get("/search/stream")
@limiter.limit(f"{settings.rate_limit_search_per_minute}/minute")
async def search_stream_get(
    request: Request,
    query: str = Query(..., min_length=1, max_length=500)
):
    _check_injection(query)
    return StreamingResponse(
        search_service.search_stream(query),
        media_type="text/event-stream"
    )


@app.get("/cache/stats")
async def cache_stats():
    return search_service.cache.get_stats()


@app.delete("/cache")
async def clear_cache():
    cleared = search_service.cache.clear_expired()
    search_service.cache.enforce_max_entries(100)
    return {"message": f"Cleared {cleared} expired entries"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
