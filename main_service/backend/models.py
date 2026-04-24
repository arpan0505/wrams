from sqlalchemy import Column, Integer, Float, String, BigInteger
from .database import Base

class EmbkFrameInf(Base):
    __tablename__ = "embk_frame_inf"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    latitude = Column(Float)
    longitude = Column(Float)
    e_id = Column(BigInteger)
    timestamp = Column(Float)
    filename = Column(String)
