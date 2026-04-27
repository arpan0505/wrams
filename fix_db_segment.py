import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("Enabling auto-increment for embk_frame_geom_inf_segment.id...")
    # Create sequence and set as default
    db.execute(text("CREATE SEQUENCE IF NOT EXISTS embk_frame_geom_inf_segment_id_seq"))
    db.execute(text("ALTER TABLE embk_frame_geom_inf_segment ALTER COLUMN id SET DEFAULT nextval('embk_frame_geom_inf_segment_id_seq')"))
    
    # Also clean up any partial data for e_id 370 to allow a fresh start
    print("Cleaning up old segments for e_id 370...")
    db.execute(text("DELETE FROM embk_frame_geom_inf_segment WHERE e_id = 370"))
    
    db.commit()
    print("Success: DB schema updated and old data cleaned.")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
