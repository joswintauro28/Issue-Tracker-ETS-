"""FastAPI application entrypoint.

Run locally from the ``backend`` directory with:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, dashboard, issues, users
from app.core.config import settings
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Simple dev-friendly bootstrap: create missing tables on startup.
    # For PostgreSQL deployments prefer Alembic migrations instead.
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Full-stack Issue Tracker backend (FastAPI + SQLAlchemy + JWT).",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_PREFIX}/users", tags=["users"])
app.include_router(issues.router, prefix=f"{settings.API_PREFIX}/issues", tags=["issues"])
app.include_router(dashboard.router, prefix=f"{settings.API_PREFIX}/dashboard", tags=["dashboard"])


@app.get(f"{settings.API_PREFIX}/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Simple liveness probe."""
    return {"status": "ok"}
