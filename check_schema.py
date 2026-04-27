from core.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
columns = inspector.get_columns('embk_frame_geom_inf')
for column in columns:
    print(column['name'])
