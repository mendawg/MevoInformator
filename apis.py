import numpy as np
import requests
import pandas as pd
from haversine import haversine_distance
from load_location import get_env

MEVO_HEADERS = {
    "Client-Identifier": "mendawg"
}
MEVO_ALL_STATIONS_URL = "https://gbfs.urbansharing.com/rowermevo.pl/station_information.json"
MEVO_ALL_BIKES_STATIONS_URL = "https://gbfs.urbansharing.com/rowermevo.pl/station_status.json"

START_LAT = np.float64(get_env("START_LOCATION_LAT"))
START_LON = np.float64 (get_env("START_LOCATION_LON"))

DEST_LAT = np.float64(get_env("DEST_LOCATION_LAT"))
DEST_LON = np.float64(get_env("DEST_LOCATION_LON"))

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

try:
    response = requests.get(MEVO_ALL_STATIONS_URL, headers= MEVO_HEADERS)
    bikes_at_stations = requests.get(MEVO_ALL_BIKES_STATIONS_URL, headers=MEVO_HEADERS)

    #POBIERANIE DANYCH I SPRAWDZANIE SUKCESU
    if bikes_at_stations.status_code != 200 or response.status_code != 200:
        raise RuntimeError("Nie udalo sie pobrac stacji")


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

    max_bikes_at_dest = closest_dest_station["capacity"]
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

    ebikes_dest = pd.DataFrame(bikes_dest.iloc[0]["vehicle_types_available"])
    all_bikes_dest = ebikes_dest["count"].sum()
    ebikes_dest = ebikes_dest[ebikes_dest["vehicle_type_id"] == "ebike"]["count"]



    print(f"Wybrane parametry: \nStacja początkowa: {start_station["name"].iloc[0]}\nAdres: {start_station_address.iloc[0]}\n"
          f"Liczba dostępnych rowerów elektrycznych: {ebikes_start.iloc[0]}\n\nStacja końcowa najbliżej pkt. docelowego: {closest_dest_station["name"]}\n"
          f"Adres: {dest_station_address}\nLiczba wolnych stojaków: {closest_dest_station["num_docks_available"]}")



except RuntimeError as e:
    print(e)

