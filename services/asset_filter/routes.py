"""
API routes for the Asset Filter service.
All filter behavior is driven by the service profile JSON.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx

from core.database import get_db
from config.settings import get_settings

settings = get_settings()
profile = settings.load_profile()

router = APIRouter(prefix="/api")


@router.get("/config")
def get_filter_config():
    """
    Returns the full filter cascade config to the frontend.
    The frontend dynamically renders dropdowns based on this.
    """
    return {
        "service_name": settings.SERVICE_PROFILE,
        "display_name": profile.get("display_name", "Service"),
        "header_title": profile.get("header_title", "Asset Data Filter"),
        "vision_player_url": settings.PUBLIC_VISION_PLAYER_URL,
        "java_api_base_path": profile.get("java_api_base_path", ""),
        "id_field": profile.get("id_field", "e_id"),
        "filter_cascade": profile.get("filter_cascade", []),
    }


@router.get("/java-proxy")
async def java_proxy(path: str):
    """
    Proxies requests to the Java API to bypass CORS.
    Java URL is built from config, not hardcoded.
    """
    java_base = profile.get("java_api_base_path", "")
    java_url = f"{settings.JAVA_API_URL}{path}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(java_url)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/filters/query/{query_key}")
def run_local_query(query_key: str, request: Request, db: Session = Depends(get_db)):
    """
    Generic endpoint to run any local SQL query defined in the profile.
    Query key maps to local_queries in the profile JSON.

    Example: /api/filters/query/sub_divisions?division_id=123
    """
    local_queries = profile.get("local_queries", {})
    query_config = local_queries.get(query_key)
    if not query_config:
        raise HTTPException(
            status_code=404,
            detail=f"Query '{query_key}' not found in profile '{settings.SERVICE_PROFILE}'"
        )

    try:
        # Build params from query string
        params = {}
        for param_name in query_config.get("params", []):
            value = request.query_params.get(param_name)
            if value is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required parameter: {param_name}"
                )
            params[param_name] = value

        result = db.execute(text(query_config["sql"]), params)
        value_key = query_config.get("value_key", "id")
        text_key = query_config.get("text_key", "name")

        items = []
        for row in result:
            row_dict = row._asdict() if hasattr(row, '_asdict') else dict(row._mapping)
            items.append({
                "id": row_dict.get(value_key, ""),
                "name": row_dict.get(text_key, "Unknown"),
            })
        return items

    except HTTPException:
        raise
    except Exception as e:
        print(f"Local query '{query_key}' failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# Backward-compatible endpoint (matches old /api/filters/sub-divisions)
# ------------------------------------------------------------------
@router.get("/filters/sub-divisions")
def get_sub_divisions_compat(division_id: str, db: Session = Depends(get_db)):
    """
    Legacy endpoint kept for backward compatibility.
    Internally delegates to the generic query runner.
    """
    local_queries = profile.get("local_queries", {})
    query_config = local_queries.get("sub_divisions")
    if not query_config:
        raise HTTPException(status_code=404, detail="sub_divisions query not in profile")

    try:
        result = db.execute(text(query_config["sql"]), {"division_id": division_id})
        value_key = query_config.get("value_key", "id")
        text_key = query_config.get("text_key", "name")

        items = []
        for row in result:
            row_dict = row._asdict() if hasattr(row, '_asdict') else dict(row._mapping)
            items.append({
                "id": row_dict.get(value_key, ""),
                "name": row_dict.get(text_key, "Unknown"),
            })
        return items
    except Exception as e:
        print(f"Sub-division query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
