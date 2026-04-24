from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Reverting to PostgreSQL as requested
DATABASE_URL = "postgresql://postgres:Passw0rd@127.0.0.1:5001/wrams"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
