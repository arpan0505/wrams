"""
Shared middleware configuration.
Apply consistent CORS, error handling, etc. to any FastAPI app.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI) -> None:
    """Apply CORS middleware with permissive settings for development.
    In production behind nginx, this can be tightened."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
