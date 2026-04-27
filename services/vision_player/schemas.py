"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, field_validator
from typing import List, Optional, Union


class FrameCreate(BaseModel):
    latitude: float
    longitude: float
    e_id: int
    timestamp: Union[float, str]
    image_base64: str
    filename: str
    video_filename: Optional[str] = None

    @field_validator('timestamp', mode='before')
    def parse_timestamp(cls, v):
        # Gracefully handle both "2.0" and raw numbers
        try:
            return float(v)
        except (ValueError, TypeError):
            # If it's a full Date string that can't be a float, just return a 0
            # to prevent 422 errors while the user's browser cache updates
            return 0.0


class FrameBatch(BaseModel):
    frames: List[FrameCreate]
