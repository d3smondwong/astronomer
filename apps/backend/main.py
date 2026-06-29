"""
FastAPI app for Astronomer / Celestial Dawn BaZi calculation backend.

Runs at localhost:8000 in development, Cloud Run in production.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

# Load the repo-root .env (LLM API keys etc.) before any router/provider imports
# read os.environ. Explicit path so it works regardless of the working directory.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from apps.utils.logging import configure_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.backend.routers import chart


@asynccontextmanager
async def lifespan(app: FastAPI):
    # configure_logging() is called here (inside the ASGI lifespan) rather than at
    # module import time so that uvicorn's reload mode — which spawns a reloader
    # process + worker process, each importing this module — only creates ONE log
    # directory (for the actual worker), not three.
    configure_logging()
    yield


# Initialize FastAPI app
app = FastAPI(
    title="Astronomer API",
    description="BaZi calculation backend for Celestial Dawn",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
# In development: allow localhost:3000 (Next.js dev server)
# In production: will be set to Firebase App Hosting domain
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    # Production domains added by environment config
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chart.router)


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Astronomer API",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("apps.backend.main:app", host="0.0.0.0", port=8000, reload=True)
