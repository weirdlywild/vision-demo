from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
import asyncio
import os
from pathlib import Path
from app.api.endpoints import router
from app.services.session_manager import session_manager
from app.services.cache_manager import cache_manager
from app.config import settings
from app.middleware.security import SecurityMiddleware, limiter, rate_limit_exceeded_handler


# Background cleanup task
async def cleanup_task():
    """Periodically clean up expired sessions and cache entries."""
    while True:
        await asyncio.sleep(settings.cleanup_interval_minutes * 60)

        # Clean up expired sessions
        removed_sessions = session_manager.cleanup_expired()

        # Clean up expired cache entries
        cache_cleanup = cache_manager.cleanup_expired()

        # Log cleanup results
        print(f"Cleanup: {removed_sessions} sessions, "
              f"{cache_cleanup['exact_removed']} exact cache, "
              f"{cache_cleanup['perceptual_removed']} perceptual cache")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    print("Starting DIY Repair Diagnosis API...")
    print(f"OpenAI Model: {settings.openai_model}")
    print(f"Cache TTL: {settings.cache_ttl_seconds}s")
    print(f"Session TTL: {settings.session_ttl_minutes}m")

    # Start cleanup task
    cleanup_task_handle = asyncio.create_task(cleanup_task())

    yield

    # Shutdown
    print("Shutting down...")
    cleanup_task_handle.cancel()
    try:
        await cleanup_task_handle
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title="DIY Repair Diagnosis API",
    description="AI-powered visual diagnosis of broken household items with repair instructions",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter

# CORS middleware
allowed_origins = settings.allowed_origins.split(",") if settings.allowed_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware (authentication and referrer checking)
app.add_middleware(SecurityMiddleware)


# Exception handlers
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return await rate_limit_exceeded_handler(request, exc)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    import traceback
    print(f"ERROR: {exc}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "details": str(exc)
        }
    )


# Include routers
app.include_router(router, tags=["diagnosis"])


# Mount static files for frontend
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


# Root endpoint - serve frontend
@app.get("/")
async def root():
    """Serve the frontend application."""
    frontend_index = frontend_dir / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)

    # Fallback API info if frontend not found
    return {
        "name": "DIY Repair Diagnosis API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "diagnose": "POST /diagnose",
            "health": "GET /health",
            "docs": "GET /docs",
            "frontend": "GET / (if frontend files are present)"
        }
    }


# API info endpoint
@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": "DIY Repair Diagnosis API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "diagnose": "POST /diagnose",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    import os

    # Use PORT environment variable if available (for Railway), otherwise default to 8000
    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
