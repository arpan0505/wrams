"""
API routes for the Vision Player service.
Separated from app.py for clean modularity.
"""
import base64
import os
import httpx
from sqlalchemy import text

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from core.database import get_db
from config.settings import get_settings
from . import models, schemas

settings = get_settings()
profile = settings.load_profile()

router = APIRouter(prefix="/api")


@router.get("/config")
def get_frontend_config():
    """
    Serves runtime configuration to the frontend.
    This is the key to removing ALL hardcoded URLs from JavaScript.
    """
    return {
        "service_name": settings.SERVICE_PROFILE,
        "display_name": profile.get("display_name", "Service"),
        "player_title": profile.get("player_title", "VisionPlayer"),
        "player_subtitle": profile.get("player_subtitle", ""),
        "id_field": profile.get("id_field", "e_id"),
        "id_label": profile.get("id_label", "E_ID"),
        "java_api_base_path": profile.get("java_api_base_path", ""),
        "upload_url": settings.PUBLIC_UPLOAD_URL,
        "filter_service_url": settings.PUBLIC_ASSET_FILTER_URL,
        "vision_player_url": settings.PUBLIC_VISION_PLAYER_URL,
    }


@router.post("/frames/batch")
def receive_frames_batch(
    batch: schemas.FrameBatch, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Receive and store a batch of captured frames."""
    storage_dir = settings.FRAMES_STORAGE_DIR
    os.makedirs(storage_dir, exist_ok=True)
    
    # Get the E_ID from the first frame in the batch
    target_e_id = batch.frames[0].e_id if batch.frames else None

    print(f"Received batch of {len(batch.frames)} frames for E_ID: {target_e_id}")
    try:
        results = []
        for i, frame in enumerate(batch.frames):
            # Save base64 image to disk
            if frame.image_base64:
                try:
                    header, encoded = frame.image_base64.split(",", 1) if "," in frame.image_base64 else ("", frame.image_base64)
                    image_data = base64.b64decode(encoded)
                    file_path = os.path.join(storage_dir, frame.filename)
                    with open(file_path, "wb") as f:
                        f.write(image_data)
                except Exception as ex:
                    print(f"Failed to save image {frame.filename} to disk: {ex}")

            # 1. Insert into frame table
            new_inf = models.FrameInf(
                latitude=frame.latitude,
                longitude=frame.longitude,
                e_id=frame.e_id,
                timestamp=frame.timestamp,
                filename=frame.filename,
            )
            db.add(new_inf)
            db.flush()
            results.append(new_inf.id)

            # 2. ALSO insert into the legacy geometry table (required by emb_frame_geom.py)
            db.execute(
                text("""
                    INSERT INTO embk_frame_geom_inf (frame_id, e_id, geom)
                    VALUES (:f_id, :e_id, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                """),
                {
                    "f_id": new_inf.id,
                    "e_id": frame.e_id,
                    "lon": frame.longitude,
                    "lat": frame.latitude
                }
            )
            if i % 10 == 0:
                print(f"Processed {i+1}/{len(batch.frames)} frames in DB...")

        db.commit()
        print(f"Successfully committed {len(results)} frames to DB.")

        # 3. FORWARD to Remote Server (Legacy Behavior)
        if settings.REMOTE_UPLOAD_URL:
            print(f"Queueing remote forward task to {settings.REMOTE_UPLOAD_URL}...")
            background_tasks.add_task(forward_to_remote_server, batch.dict())

        # Trigger spatial processing in the background
        if target_e_id:
            print(f"Queueing spatial processing task for E_ID {target_e_id}...")
            background_tasks.add_task(trigger_spatial_processing, target_e_id)

        return {"status": "success", "processed_count": len(results)}

    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"Batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def forward_to_remote_server(payload: dict):
    """Forwards the frame batch to the legacy remote storage server."""
    url = settings.REMOTE_UPLOAD_URL
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"Forwarding frame batch to remote server: {url}...")
            response = await client.post(url, json=payload)
            if response.is_success:
                print("Successfully forwarded frames to remote server.")
            else:
                print(f"Remote server returned error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Failed to forward frames to remote server: {e}")


async def trigger_spatial_processing(e_id: int):
    """Background task to run the embankment geometry alignment script."""
    try:
        print(f"Starting background spatial processing for e_id: {e_id}...")
        from scripts.emb_frame_geom import doSetEmbkFrameGeomInfo
        await doSetEmbkFrameGeomInfo(e_id)
        print(f"Successfully finished spatial processing for e_id: {e_id}")
    except Exception as e:
        print(f"Background spatial processing failed for e_id {e_id}: {e}")


@router.get("/frames")
def get_frames(db: Session = Depends(get_db)):
    """Returns all frames."""
    return db.query(models.FrameInf).all()


@router.get("/java-proxy")
async def java_proxy(path: str):
    """
    Proxies requests to the Java API service to bypass CORS.
    The Java URL is built from config, not hardcoded.
    """
    import httpx

    java_url = f"{settings.JAVA_API_URL}{path}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(java_url)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
