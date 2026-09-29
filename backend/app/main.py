"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.database import create_tables, SessionLocal
from app.db.seed import seed_database
from app.rag.pipeline import load_index

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Create database tables
    create_tables()
    logger.info("Database tables created/verified")
    # Seed demo data
    db = SessionLocal()
    try:
        results = seed_database(db)
        logger.info(f"Seed results: {results}")
    finally:
        db.close()
    # Try to load existing RAG index
    if load_index():
        logger.info("RAG index loaded from disk")
    else:
        logger.info("No RAG index found — use /api/knowledge/reindex to build it")
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered restaurant customer support and operations agent",
    docs_url="/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Centralized exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception (%s)", type(exc).__name__)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# Include routers
from app.api import auth, orders, tickets, agent, knowledge, automation, dashboard, health

app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(tickets.router)
app.include_router(agent.router)
app.include_router(knowledge.router)
app.include_router(automation.router)
app.include_router(dashboard.router)
app.include_router(health.router)


@app.get("/api/docs", include_in_schema=False)
def api_docs_compatibility():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
    )


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }
