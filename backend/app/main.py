"""
Enterprise AI Assistant - Main Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.chat import router as chat_router
from api.v1.auth import router as auth_router
from api.v1.admin import router as admin_router
from core.config import settings
from core.logging import setup_logging, get_logger
from db.session import init_db, close_db


# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Enterprise AI Assistant", version=settings.app_version)
    
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down Enterprise AI Assistant")
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered enterprise knowledge assistant with MCP-based tool orchestration",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(chat_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)


@app.get("/")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version
    }


@app.get("/health")
def health_detailed():
    """Detailed health check."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "ai_provider": settings.ai_provider
    }
