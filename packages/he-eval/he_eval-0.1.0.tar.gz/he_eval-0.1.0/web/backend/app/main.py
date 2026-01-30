"""FastAPI application for human evaluation coordination."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import assignments, auth, export, sessions, tasks, users
from app.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    # Create data directory if needed
    Path("./data").mkdir(exist_ok=True)
    settings.eval_logs_dir.mkdir(parents=True, exist_ok=True)

    # Initialize database tables
    await init_db()

    yield

    # Shutdown (nothing to do)


app = FastAPI(
    title="Human Eval API",
    description="Backend API for human evaluation coordination",
    version="0.1.0",
    lifespan=lifespan,
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
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(assignments.router)
app.include_router(sessions.router)
app.include_router(tasks.router)
app.include_router(export.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "human-eval-backend"}


@app.get("/health")
async def health():
    """Health check for load balancers."""
    return {"status": "healthy"}
