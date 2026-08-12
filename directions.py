import pandas as pd

from helpers.load_location import get_env
import requests
from datetime import datetime


BIKE_PROFILE = "mapbox/cycling"
CAR_PROFILE = "mapbox/driving-traffic"

START_LAT_MEVO = get_env("MEVO_START_LOCATION_LAT")
START_LON_MEVO = get_env("MEVO_START_LOCATION_LON")

MAPBOX_API = get_env("MAPBOX_API")


DEST_LAT = get_env("DEST_LOCATION_LAT")
DEST_LON = get_env("DEST_LOCATION_LON")


def get_travel_duration(profile:str, start_lat : str, start_lon : str, dest_lat : str, dest_lon : str, dep_h : int = 7 ,
                        dep_m : int = 20, dep_s : int = 0):
    profile = profile.lower()
    params = {}
    if profile == "car":
        t = datetime.now().astimezone().replace(
            hour=dep_h,
            minute=dep_m,
            second=dep_s,
            microsecond=0
        )
        params['depart_at'] = t.isoformat(timespec='seconds')
        profile = "driving-traffic"

    elif profile == "bike":
        profile = "cycling"

    else:
        raise RuntimeError("Bledny profil")


    mapbox_url = (f"https://api.mapbox.com/directions/v5/mapbox/{profile}/{start_lon},{start_lat};{dest_lon},{dest_lat}"
                  f"?access_token={MAPBOX_API}")
    directions = requests.get(mapbox_url,params = params)
    if directions.status_code == 200:
        data = directions.json()
        data_df = pd.DataFrame(data["routes"])
        return pd.DataFrame({
            "distance" : data_df["distance"],
            "duration_s" : data_df["duration"],
            "duration_typical" : data_df["duration_typical"] if profile == "driving-traffic" else pd.NA
        })
    raise RuntimeError(f"Nie udalo sie pobrac czasu podrozy. Kod: {directions.status_code}")

