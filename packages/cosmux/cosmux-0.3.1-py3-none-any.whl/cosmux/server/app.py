"""FastAPI application"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from cosmux.db.engine import create_db_and_tables
from cosmux.server.routes import health, sessions, chat, websocket, auth
from cosmux.server.static import router as static_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (cleanup if needed)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="Cosmux API",
        description="AI Coding Agent Widget for Web Development",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS Middleware - allow all for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # API Routes
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(websocket.router, prefix="/api/chat", tags=["websocket"])

    # Static files and widget
    app.include_router(static_router, tags=["static"])

    # Mount static files directory if it exists
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app


# Create app instance
app = create_app()
