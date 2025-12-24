import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .middleware.logging import RequestLoggingMiddleware
from .routers import chat

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Compliance Gateway",
    description="OpenAI-compatible proxy for AI compliance and audit logging",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(chat.router, prefix="/v1", tags=["Chat Completions"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "gateway",
        "provider": settings.ai_provider,
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "AI Compliance Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


