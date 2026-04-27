"""
Asset Filter — FastAPI application factory.
This is the entry point for the asset selection/filtering service.

Run standalone:
    uvicorn services.asset_filter.app:app --port 8001 --reload

Or via unified runner:
    python run.py --service asset_filter
"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response

from core.middleware import setup_cors
from config.settings import get_settings
from .routes import router

settings = get_settings()
profile = settings.load_profile()

app = FastAPI(title=profile.get("header_title", "Asset Filter"))

# Apply shared middleware
setup_cors(app)

# Register API routes
app.include_router(router)

# Favicon handler
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# Mount frontend — MUST be last
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
