from sqlalchemy import create_engine, text
import json

DATABASE_URL = "postgresql://postgres:Passw0rd@127.0.0.1:5001/wrams"
engine = create_engine(DATABASE_URL)

def get_schema():
    with engine.connect() as conn:
        # Check columns of v_wrams_asset_embankment
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'v_wrams_asset_embankment'
        """))
        columns = [{"name": row[0], "type": row[1]} for row in result]
        
        # Get some sample data
        sample = conn.execute(text("SELECT * FROM v_wrams_asset_embankment LIMIT 5"))
        keys = sample.keys()
        data = [dict(zip(keys, row)) for row in sample]
        
        return {"columns": columns, "sample": data}

if __name__ == "__main__":
    print(json.dumps(get_schema(), indent=2, default=str))
