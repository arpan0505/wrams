import base64
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from . import models, schemas
from .database import engine, get_db

from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="WRAMS Main Service")

# Static file logic moved to bottom

# Create tables in DB
models.Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Local storage for frames (now within main_service/backend/)
STORAGE_DIR = "frames_storage"
os.makedirs(STORAGE_DIR, exist_ok=True)


@app.post("/api/frames/batch")
def receive_frames_batch(batch: schemas.FrameBatch, db: Session = Depends(get_db)):
    try:
        results = []
        for frame in batch.frames:
            # 1. Save Image to Local Storage
            clean_base64 = frame.image_base64.split(",")[1] if "," in frame.image_base64 else frame.image_base64
            img_data = base64.b64decode(clean_base64)
            filepath = os.path.join(STORAGE_DIR, frame.filename)
            with open(filepath, "wb") as f:
                f.write(img_data)

            # 2. Insert into embk_frame_inf
            new_inf = models.EmbkFrameInf(
                latitude=frame.latitude,
                longitude=frame.longitude,
                e_id=frame.e_id,
                timestamp=frame.timestamp,
                filename=frame.filename
            )
            db.add(new_inf)
            db.flush()
            results.append(new_inf.id)

        db.commit()
        return {"status": "success", "processed_count": len(results)}

    except Exception as e:
        db.rollback()
        print(f"Batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/frames")
def get_frames(db: Session = Depends(get_db)):
    """
    Returns all frames.
    """
    return db.query(models.EmbkFrameInf).all()

# --- MOVED TO BOTTOM ---
from fastapi.responses import Response

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# Mount Frontend files to the root /
# This must be at the end so it doesn't block /api routes
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
