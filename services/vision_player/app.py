"""
Vision Player — FastAPI application factory.
This is the entry point for the frame-capture service.

Run standalone:
    uvicorn services.vision_player.app:app --port 8000 --reload

Or via unified runner:
    python run.py --service vision_player
"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response

from core.database import engine, Base
from core.middleware import setup_cors
from config.settings import get_settings
from .routes import router
from . import models  # noqa: F401 — ensures model is registered with Base

settings = get_settings()
profile = settings.load_profile()

app = FastAPI(title=profile.get("player_title", "VisionPlayer"))

# Apply shared middleware
setup_cors(app)

# Create tables in DB (safe — won't overwrite existing)
Base.metadata.create_all(bind=engine)

# Register API routes
app.include_router(router)

# Favicon handler (prevents 404 noise in logs)
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# Mount frontend — MUST be last so it doesn't block /api routes
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
