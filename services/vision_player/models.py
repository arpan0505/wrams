"""
Dynamic SQLAlchemy model — table name comes from service profile config.
This means the same code can store frames in 'embk_frame_inf' for WRAMS
or 'road_frame_inf' for Road PMS, just by changing SERVICE_PROFILE in .env.
"""
from sqlalchemy import Column, Float, String, BigInteger
from core.database import Base
from config.settings import get_settings

settings = get_settings()
profile = settings.load_profile()


class FrameInf(Base):
    """Generic frame information model. Table name is set by the profile."""
    __tablename__ = profile.get("frame_table", "frame_inf")

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    latitude = Column(Float)
    longitude = Column(Float)
    # Dynamic ID column name from profile (e_id for WRAMS, road_id for Road)
    e_id = Column(BigInteger)
    timestamp = Column(Float)
    filename = Column(String)
