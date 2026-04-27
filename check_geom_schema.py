import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("Columns in embk_frame_geom_inf:")
    r = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'embk_frame_geom_inf'"))
    for row in r:
        print(f" - {row[0]}: {row[1]}")
finally:
    db.close()
