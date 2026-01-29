import enum
import json
import dateutil.parser
import geopandas as gpd
import shapely.geometry
import typer
from typing import Any

class OutputTypes(enum.Enum):
    geotiff = 'geotiff'
    png = 'png'
    netcdf = 'netcdf'
    json = 'json'
    json_v2 = 'json_v2'
    csv = 'csv'

class Region(str, enum.Enum):
    aus = "aus"
    eu = "eu"
    us = "us"

regions = {
    Region.aus : {
        "name" : "australia-southeast1", 
        "url" : "https://terrakio-server-candidate-573248941006.australia-southeast1.run.app", 
        "bucket" : "terrakio-mass-requests"
    },
    
    Region.eu : {
        "name" : "europe-west4", 
        "url" : "https://terrakio-server-candidate-573248941006.europe-west4.run.app", 
        "bucket" : "terrakio-mass-requests-eu"
    },
    
    Region.us : {
        "name" : "us-central1", 
        "url" : "https://terrakio-server-candidate-573248941006.us-central1.run.app", 
        "bucket" : "terrakio-mass-requests-us"
    },
}


class Dataset_Dtype(enum.Enum):
    uint8 = 'uint8'
    float32 = 'float32'


def get_bounds(aoi, crs, to_crs = None):
    gdf : gpd.GeoDataFrame = gpd.read_file(aoi)
    gdf = gdf.set_crs(crs, allow_override=True)
    if to_crs:
        gdf = gdf.to_crs(to_crs)
    bounds = gdf.geometry[0].bounds
    return *bounds, gdf


def validate_date(date: str) -> str:
    try:
        date = dateutil.parser.parse(date)
        return date
    except ValueError:
        print(f"Invalid date: {date}")
        raise typer.BadParameter(f"Invalid date: {date}")


def make_json_serializable(obj):
    """Convert non-JSON-serializable types to JSON-serializable equivalents."""
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    elif hasattr(obj, 'isoformat'):  # Timestamp, datetime, date, time
        return obj.isoformat()
    elif hasattr(obj, 'item'):  # numpy types
        return obj.item()
    else:
        return obj

