import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Get max ID
    r = db.execute(text("SELECT MAX(id) FROM embk_frame_geom_inf_segment")).first()
    max_id = r[0] if r and r[0] is not None else 0
    print(f"Current Max ID: {max_id}")
    
    # Sync sequence
    new_start = max_id + 1
    print(f"Restarting sequence at {new_start}...")
    db.execute(text(f"ALTER SEQUENCE embk_frame_geom_inf_segment_id_seq RESTART WITH {new_start}"))
    
    db.commit()
    print("Sequence synchronized.")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
