import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    for table in ['embk_frame_inf', 'embk_frame_geom_inf', 'embk_frame_geom_inf_segment']:
        try:
            r = db.execute(text(f"SELECT count(*) FROM {table} WHERE e_id = 370")).first()
            print(f"Count in {table}: {r[0]}")
        except Exception as e:
            print(f"Error checking {table}: {e}")
finally:
    db.close()
