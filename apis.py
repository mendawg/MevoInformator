import numpy as np
import requests
import pandas as pd
from helpers.haversine import haversine_distance
from helpers.load_location import get_env
from weather import current_weather
from directions import get_travel_duration
from datetime import datetime
from log_api import  _init_db, log_api


MEVO_HEADERS = {
    "Client-Identifier": "mendawg"
}
MEVO_ALL_STATIONS_URL = "https://gbfs.urbansharing.com/rowermevo.pl/station_information.json"
MEVO_ALL_BIKES_STATIONS_URL = "https://gbfs.urbansharing.com/rowermevo.pl/station_status.json"

START_LAT = np.float64(get_env("MEVO_START_LOCATION_LAT"))
START_LON = np.float64 (get_env("MEVO_START_LOCATION_LON"))

START_LAT_CAR = get_env("CAR_START_LOCATION_LAT")
START_LON_CAR = get_env("CAR_START_LOCATION_LON")

DEST_LAT = np.float64(get_env("DEST_LOCATION_LAT"))
DEST_LON = np.float64(get_env("DEST_LOCATION_LON"))

MAPBOX_API = get_env("MAPBOX_API")


RADIUS = 400

found_dest = True

def check_station(station_type: str, station: pd.Series) -> bool:
    station_type = station_type.lower()
    if station_type not in ("start", "dest"):
        raise RuntimeError("Wrong station type")

    if pd.notna(station["station_id"]) and station["is_installed"]:
        if station_type == "start":
            bikes = pd.DataFrame(station["vehicle_types_available"])
            if bikes.empty:
                return False
            ebike_count = bikes.loc[bikes["vehicle_type_id"] == "ebike", "count"].sum()
            return bool(station["is_renting"]) and ebike_count >= 1
        else:
            return bool(station["is_returning"])
    return False

def get_data():

    try:
        _init_db()

        response = requests.get(MEVO_ALL_STATIONS_URL, headers= MEVO_HEADERS)
        bikes_at_stations = requests.get(MEVO_ALL_BIKES_STATIONS_URL, headers=MEVO_HEADERS)

        #POBIERANIE DANYCH I SPRAWDZANIE SUKCESU
        if bikes_at_stations.status_code != 200 or response.status_code != 200:
            raise RuntimeError("Nie udalo sie pobrac stacji")

        log_api("mevo_bikes", START_LAT, START_LON, DEST_LAT, DEST_LON)
        log_api("mevo_stations", START_LAT, START_LON, DEST_LAT, DEST_LON)

        data_bikes = bikes_at_stations.json()["data"]["stations"]
        bikes_df = pd.DataFrame(data_bikes)

        stations = response.json()["data"]["stations"]
        stations_df = pd.DataFrame(stations)

        start_station = stations_df[
            np.isclose(stations_df["lat"], START_LAT, atol=1e-6) &
            np.isclose(stations_df["lon"], START_LON, atol=1e-6)
            ]

        if start_station.empty:
            raise RuntimeError("Start station not okay")

        dest_stations = stations_df[
            haversine_distance(DEST_LAT, DEST_LON, stations_df["lat"], stations_df["lon"]) <= RADIUS
            ].copy()

        dest_stations["dist"] = haversine_distance(dest_stations["lat"], dest_stations["lon"], DEST_LAT, DEST_LON)
        dest_stations = dest_stations.merge(bikes_df[["station_id", "num_docks_available"]], on= "station_id", how = "left")

        dest_stations = dest_stations[dest_stations["num_docks_available"] >= 1]
        if dest_stations.empty:
            raise RuntimeError("Wszystkie stacje w okolicy pkt. docelowego są pełne!")

        closest_dest_station = dest_stations.sort_values(["dist"],ascending = True).iloc[0]

        # max_bikes_at_dest = closest_dest_station["capacity"]
        dest_station_address = closest_dest_station["address"]

        start_station_address = start_station["address"]

        start_id = start_station.iloc[0]["station_id"]
        dest_id = closest_dest_station["station_id"]

        bikes_start = bikes_df[bikes_df["station_id"] == start_id]
        bikes_dest = bikes_df[bikes_df["station_id"] == dest_id]

        if bikes_start.empty or not check_station("start", bikes_start.iloc[0]):
            raise RuntimeError("Bledna stacja poczatkowa")

        if not check_station("dest", bikes_dest.iloc[0]):
            raise RuntimeError("Bledna stacja koncowa")

        ebikes_start = pd.DataFrame(bikes_start.iloc[0]["vehicle_types_available"])
        ebikes_start = ebikes_start[ebikes_start["vehicle_type_id"] == "ebike"]["count"]

        # ebikes_dest = pd.DataFrame(bikes_dest.iloc[0]["vehicle_types_available"])
        # all_bikes_dest = ebikes_dest["count"].sum()
        # ebikes_dest = ebikes_dest[ebikes_dest["vehicle_type_id"] == "ebike"]["count"]
        #
        # print(f"Godzina: {datetime.now()}")
        #



        start_weather = current_weather(START_LAT,START_LON)
        log_api("openweather", START_LAT, START_LON, DEST_LAT, DEST_LON)

        dest_weather = current_weather(DEST_LAT, DEST_LON)
        log_api("openweather", DEST_LAT, DEST_LON, START_LAT, START_LON)




        try:
            bike_travel = get_travel_duration("bike", str(START_LAT), str(START_LON), str(DEST_LAT), str(DEST_LON))
            log_api("mapbox", START_LAT, START_LON, DEST_LAT, DEST_LON)

            car_travel = get_travel_duration("car", START_LAT_CAR,START_LON_CAR, str(DEST_LAT), str(DEST_LON))
            log_api("mapbox", START_LAT_CAR, START_LON_CAR, DEST_LAT, DEST_LON)



            return pd.DataFrame([{
                "start_station" : start_station["name"].iloc[0],
                "start_station_address" : start_station_address.iloc[0],
                "available_ebikes" : ebikes_start.iloc[0],
                "closest_dest_station" : closest_dest_station["name"],
                "dest_station_address" : dest_station_address,
                "docks_available" : closest_dest_station["num_docks_available"],
                "start_location_weather" : start_weather["location"].iloc[0],
                "start_location_weather_time" : start_weather["local_time"].iloc[0],
                "start_weather_status" : start_weather["main"].iloc[0],
                "start_temp" : start_weather["temp"].iloc[0],
                "start_temp_feels_like" : start_weather["feels_like"].iloc[0],
                "start_wind_ms" : start_weather["wind"].iloc[0],
                "start_clouds_perc" : start_weather["clouds_percentage"].iloc[0],
                "dest_location_weather" : dest_weather["location"].iloc[0],
                "dest_location_weather_time" : dest_weather["local_time"].iloc[0],
                "dest_weather_status" : dest_weather["main"].iloc[0],
                "dest_temp" : dest_weather["temp"].iloc[0],
                "dest_temp_feels_like" : dest_weather["feels_like"].iloc[0],
                "dest_wind_ms" : dest_weather["wind"].iloc[0],
                "dest_clouds_perc" : dest_weather["clouds_percentage"].iloc[0],
                "bike_travel_duration_min" : round(bike_travel["duration_s"].iloc[0] / 60, 0),
                "bike_distance_km" : round(bike_travel["distance"].iloc[0] / 1000, 2),
                "car_travel_duration_min" : round(car_travel["duration_s"].iloc[0] / 60, 0),
                "car_travel_duration_min_typical" : round(car_travel["duration_typical"].iloc[0] / 60,0),
                "car_distance_km" : round(car_travel["distance"].iloc[0] / 1000,2)
            }])


        except requests.exceptions.Timeout as e:
            print(e)
        except RuntimeError as e:
            print(e)



    except RuntimeError as e:
        print(e)

