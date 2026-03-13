"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.database.db import init_db, get_db
from backend.api.routes import router as internal_router
from backend.api.platform_routes import router as platform_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup."""
    await init_db()
    yield
    # Shutdown cleanup if needed
    pass


app = FastAPI(
    title="SheGen",
    description="Women Harassment Detection & Privacy-Preserving Moderation",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,  # Custom docs below
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Platform API - only these 2 endpoints show in Test API / Swagger
app.include_router(platform_router)
# Internal routes for dashboard (hidden from docs)
app.include_router(internal_router, prefix="/api")


# Static files (logo, etc.)
_STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Standalone dashboard (no npm build required)
_DASHBOARD_PATH = _STATIC_DIR / "dashboard.html"


from fastapi.openapi.docs import get_swagger_ui_html


@app.get("/docs", include_in_schema=False)
async def swagger_ui():
    """Test API - Platform endpoints only, no schemas."""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="SheGen - Platform API",
        swagger_ui_parameters={"defaultModelsExpandDepth": -1, "docExpansion": "list"},
    )


@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    """Serve the moderation dashboard (works without frontend build)."""
    return FileResponse(_DASHBOARD_PATH)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to dashboard."""
    return RedirectResponse(url="/dashboard")


@app.get("/health", include_in_schema=False)
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "shegen"}
