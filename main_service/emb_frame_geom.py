import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from shapely.geometry import GeometryCollection, LineString, Point

import argparse
import asyncio


async def doSetEmbkFrameGeomInfo(e_id: int):
    embLayer = gpd.read_file(
        "http://103.219.61.73/geoserver/wrams/ows?"
        "service=WFS&version=1.0.0&request=GetFeature&"
        "typeName=wrams%3Av_wrams_asset_embankment&"
        "maxFeatures=500000&outputFormat=application%2Fjson"
    )
    print("Loaded embankment data...")

    embLayer.geometry.geom_type

    embLayer = embLayer[embLayer['geometry'].notnull()].copy()

    embLayer.geometry.plot()

    engine = create_engine("postgresql://postgres:Passw0rd@localhost:5001/wrams")

    query = f"SELECT * FROM embk_frame_geom_inf WHERE e_id = {e_id}"

    ebmFramegdf = gpd.read_postgis(
        query,
        engine,
        geom_col="geom"
    )

    if ebmFramegdf.crs is None:
        ebmFramegdf = ebmFramegdf.set_crs(4326)

    ebmFramegdf.geom.plot()

    if ebmFramegdf.crs != embLayer.crs:
        ebmFramegdf_utm = ebmFramegdf.to_crs(embLayer.crs)
    else:
        ebmFramegdf_utm = ebmFramegdf.copy()

    ebmFramegdf_utm_copy = ebmFramegdf_utm.copy()

    ebmFramegdf_utm_copy = ebmFramegdf_utm_copy.reset_index(drop=True)
    ebmFramegdf_utm_copy["orig_id"] = ebmFramegdf_utm_copy.index

    ebmFramegdf_utm_copy["geometry"] = ebmFramegdf_utm_copy.geom.buffer(10)

    ebmFramegdf_utm_copy = ebmFramegdf_utm_copy.set_geometry("geometry")
    ebmFramegdf_utm_copy.geometry.plot()

    pms_data_set = gpd.clip(ebmFramegdf_utm_copy, embLayer)

    pms_data_set = pms_data_set.explode(index_parts=False)
    pms_data_set = pms_data_set.reset_index(drop=True)

    pms_data_set.plot()

    pms_data_set["centroid"] = pms_data_set.geometry.centroid

    pms_data_set

    try:
        pms_data_set.to_postgis(
            name="embk_frame_geom_inf_segment",
            con=engine,
            if_exists="append",
            index=False
        )
        print("Data successfully written to embk_frame_geom_inf_segment table.")
    except Exception as e:
        print(f"Failed to write data: {e}")

def main():
    parser = argparse.ArgumentParser(description="Process embankment data")
    parser.add_argument("--e_id", type=int, required=True, help="Embankment ID")

    args = parser.parse_args()

    asyncio.run(doSetEmbkFrameGeomInfo(args.e_id))

if __name__ == "__main__":
    main()