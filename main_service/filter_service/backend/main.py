from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import os
import httpx

app = FastAPI(title="WRAMS Filter Service")

# Database connection for the SQL query
DATABASE_URL = "postgresql://postgres:Passw0rd@127.0.0.1:5001/wrams"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/filters/sub-divisions")
def get_sub_divisions(division_id: str, db: Session = Depends(get_db)):
    try:
        query = text("""
            SELECT a.* FROM (
                SELECT JRDCN_CODE, JRDCN_SHORT_CODE, JRDCN_NAME, PJM_ID,
                CASE WHEN JRDCN_NAME LIKE 'NONPW%' THEN 'ZZZZZZ' ELSE JRDCN_NAME END AS ordercolumn
                FROM JRDCN_MST 
                WHERE EXPIRED_DATE IS NULL 
                AND JRDCN_CODE IN (SELECT JRDCN_CODE FROM JRDCN_ACSBL_INF WHERE USR_CODE = 'admin')
            ) a 
            WHERE PJM_ID = :division_id 
            ORDER BY a.ordercolumn
        """)
        result = db.execute(query, {"division_id": division_id})
        sub_divisions = []
        for row in result:
            sub_divisions.append({"id": row.jrdcn_code, "name": row.jrdcn_name})
        return sub_divisions
    except Exception as e:
        print(f"Sub-division query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/java-proxy")
async def java_proxy(path: str):
    """
    Proxies requests to the Java service to bypass CORS issues.
    """
    java_url = f"http://localhost:49001{path}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(java_url)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import Response

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# Mount frontend
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
