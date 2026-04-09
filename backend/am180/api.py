"""am180 FastAPI application.

Phase 1: minimal app with a single /health endpoint so we can prove the
backend boots and serves requests. Real /api/* endpoints arrive in Phase 2.
"""
from fastapi import FastAPI

app = FastAPI(title="am180", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe. Returns {"status": "ok"} when the server is up."""
    return {"status": "ok"}
