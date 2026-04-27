"""
Embankment Frame Geometry Processing Script.
Moved from main_service/ to scripts/ for modularity.

Usage:
    python scripts/emb_frame_geom.py --e_id 123
"""
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from shapely.geometry import GeometryCollection, LineString, Point

import argparse
import asyncio
import os
import sys

# Add project root to path so we can import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import get_settings

settings = get_settings()


async def doSetEmbkFrameGeomInfo(e_id: int):
    print(f"Fetching embankment layers from GeoServer for e_id: {e_id}...")
    try:
        embLayer = gpd.read_file(
            "http://103.219.61.73/geoserver/wrams/ows?"
            "service=WFS&version=1.0.0&request=GetFeature&"
            "typeName=wrams%3Av_wrams_asset_embankment&"
            "maxFeatures=500000&outputFormat=application%2Fjson",
            timeout=30
        )
    except Exception as e:
        print(f"Error fetching GeoServer data: {e}")
        return

    if embLayer.empty:
        print("Warning: Embankment layer is empty from GeoServer.")
        return

    embLayer = embLayer[embLayer['geometry'].notnull()].copy()
    if embLayer.empty:
        print("Warning: No valid geometries in embankment layer.")
        return

    # Use DB URL from config instead of hardcoded
    engine = create_engine(settings.DATABASE_URL)

    print(f"Reading frame geometry from database for e_id: {e_id}...")
    query = f"SELECT * FROM embk_frame_geom_inf WHERE e_id = {e_id}"
    
    try:
        ebmFramegdf = gpd.read_postgis(
            query,
            engine,
            geom_col="geom"
        )
    except Exception as e:
        print(f"Error reading from database: {e}")
        return

    if ebmFramegdf.empty:
        print(f"No frame geometry found for e_id: {e_id}. Skipping.")
        return

    if ebmFramegdf.crs is None:
        ebmFramegdf = ebmFramegdf.set_crs(4326)

    if ebmFramegdf.crs != embLayer.crs:
        ebmFramegdf_utm = ebmFramegdf.to_crs(embLayer.crs)
    else:
        ebmFramegdf_utm = ebmFramegdf.copy()

    ebmFramegdf_utm_copy = ebmFramegdf_utm.copy()
    ebmFramegdf_utm_copy = ebmFramegdf_utm_copy.reset_index(drop=True)
    ebmFramegdf_utm_copy["orig_id"] = ebmFramegdf_utm_copy.index

    # Create 10m buffer for clipping
    ebmFramegdf_utm_copy["geometry"] = ebmFramegdf_utm_copy.geom.buffer(10)
    ebmFramegdf_utm_copy = ebmFramegdf_utm_copy.set_geometry("geometry")

    print(f"Clipping frame data with asset layers...")
    pms_data_set = gpd.clip(ebmFramegdf_utm_copy, embLayer)

    if pms_data_set.empty:
        print(f"No overlapping geometry found after clipping for e_id: {e_id}.")
        return

    pms_data_set = pms_data_set.explode(index_parts=False)
    pms_data_set = pms_data_set.reset_index(drop=True)

    # Calculate centroids
    pms_data_set["centroid"] = pms_data_set.geometry.centroid

    print(f"Writing {len(pms_data_set)} segments back to database...")
    try:
        # 1. Clear old segments for this e_id to avoid duplicates/conflicts
        with engine.begin() as conn:
            conn.execute(text(f"DELETE FROM embk_frame_geom_inf_segment WHERE e_id = {e_id}"))

        # 2. Remove the 'id' column from the dataframe if it exists. 
        # This allows the database to use its auto-increment sequence for new IDs.
        if 'id' in pms_data_set.columns:
            pms_data_set = pms_data_set.drop(columns=['id'])

        # 3. Save to database
        pms_data_set.to_postgis(
            name="embk_frame_geom_inf_segment",
            con=engine,
            if_exists="append",
            index=False
        )
        print("Data successfully written to embk_frame_geom_inf_segment table.")
    except Exception as e:
        print(f"Failed to write data to database: {e}")

def main():
    parser = argparse.ArgumentParser(description="Process embankment data")
    parser.add_argument("--e_id", type=int, required=True, help="Embankment ID")

    args = parser.parse_args()

    asyncio.run(doSetEmbkFrameGeomInfo(args.e_id))

if __name__ == "__main__":
    main()
