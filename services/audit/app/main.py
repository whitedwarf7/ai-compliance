import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import logs, export, violations, auth, reports

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Compliance Audit Service",
    description="Audit log management for AI compliance platform",
    version="3.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(logs.router, prefix="/api/v1/logs", tags=["Audit Logs"])
app.include_router(export.router, prefix="/api/v1/logs/export", tags=["Export"])
app.include_router(violations.router, prefix="/api/v1/violations", tags=["Violations"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "audit",
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "AI Compliance Audit Service",
        "version": "3.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "auth": "/api/v1/auth",
            "logs": "/api/v1/logs",
            "export": "/api/v1/logs/export/csv",
            "violations": "/api/v1/violations",
            "violations_summary": "/api/v1/violations/summary",
            "reports": "/api/v1/reports",
        },
    }
