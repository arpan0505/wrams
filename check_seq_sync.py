from sqlalchemy import text
from core.database import engine

with engine.connect() as conn:
    # Check default value for id column
    res = conn.execute(text("""
        SELECT column_default 
        FROM information_schema.columns 
        WHERE table_name = 'embk_frame_geom_inf' AND column_name = 'id'
    """))
    print(f"Default: {res.scalar()}")

    # Check max id
    res = conn.execute(text("SELECT MAX(id) FROM embk_frame_geom_inf"))
    max_id = res.scalar() or 0
    print(f"Max ID: {max_id}")

    # Check sequence value if it exists
    try:
        res = conn.execute(text("SELECT nextval('embk_frame_geom_inf_id_seq')"))
        seq_val = res.scalar()
        print(f"Seq Val (next): {seq_val}")
    except Exception as e:
        print(f"No sequence or error: {e}")
