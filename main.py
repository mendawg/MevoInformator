import sqlite3
import pandas as pd
from apis import get_data
from helpers.load_location import get_env
from requests.auth import HTTPBasicAuth
import requests

NTFY_USER = get_env("NTFY_USER")
NTFY_PASSWORD = get_env("NTFY_PASS")
SERV = get_env("SERVER")
NTFY_URL = f"http://{SERV}.local/mevo-updates"



def init_db():
    conn = sqlite3.connect("trips.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_date TEXT DEFAULT CURRENT_TIMESTAMP,
            start_station TEXT,
            start_station_address TEXT,
            available_ebikes INTEGER,
            closest_dest_station TEXT,
            dest_station_address TEXT,
            docks_available INTEGER,
            start_location_weather TEXT,
            start_location_weather_time TEXT,
            start_weather_status TEXT,
            start_temp REAL,
            start_temp_feels_like REAL,
            start_wind_ms REAL,
            start_clouds_perc REAL,
            dest_location_weather TEXT,
            dest_location_weather_time TEXT,
            dest_weather_status TEXT,
            dest_temp REAL,
            dest_temp_feels_like REAL,
            dest_wind_ms REAL,
            dest_clouds_perc REAL,
            bike_travel_duration_min REAL,
            bike_distance_km REAL,
            car_travel_duration_min REAL,
            car_travel_duration_min_typical REAL,
            car_distance_km REAL
        );
    """)
    conn.commit()
    conn.close()

def generate_notification(data : pd.DataFrame):
    row = data.iloc[0]
    return f"""Wybrane parametry: 
Stacja początkowa: {row["start_station"]}
Adres: {row["start_station_address"]}
Liczba dostępnych rowerów elektrycznych: {row["available_ebikes"]}
Stacja końcowa najbliżej pkt. docelowego: {row["closest_dest_station"]}
Adres: {row["dest_station_address"]}
Liczba wolnych stojaków: {row["docks_available"]} 
Pogoda w miejscu startowym {row["start_location_weather"]}:
Pogoda z godziny: {row["start_location_weather_time"]}
Stan: {row["start_weather_status"]}
Temperatura: {row["start_temp"]}
Odczuwalna temperatura: {row["start_temp_feels_like"]}
Wiatr (m/s): {row["start_wind_ms"]}
Zachmurzenie (%): {row["start_clouds_perc"]}
Pogoda w miejscu docelowym {row["dest_location_weather"]}:
Pogoda z godziny: {row["dest_location_weather_time"]}
Stan: {row["dest_weather_status"]}
Temperatura: {row["dest_temp"]}
Odczuwalna temperatura: {row["dest_temp_feels_like"]}
Wiatr (m/s): {row["dest_wind_ms"]}
Zachmurzenie (%): {row["dest_clouds_perc"]}
Czas podróży rowerem: {row["bike_travel_duration_min"]} minut
Dystans: {row["bike_distance_km"]} km
Czas podróży samochodem: {row["car_travel_duration_min"]} minut
Typowy czas: {row["car_travel_duration_min_typical"]} minut
Dystans: {row["car_distance_km"]} km"""

def send(message: str, title: str = "Mevo Update"):
    requests.post(
        NTFY_URL,
        data=message.encode("utf-8"),
        auth=HTTPBasicAuth(NTFY_USER, NTFY_PASSWORD),
        headers={"Title": title}
    )

def save_trip(trip : pd.DataFrame):
    conn = sqlite3.connect("other/trips.db")
    try:
        trip.to_sql("trips", conn, if_exists = "append", index = False)
        conn.commit()
    except sqlite3.IntegrityError as e :
        print(f"Integrity Error {e}")
        conn.rollback()
    except sqlite3.OperationalError as e:
        print(f"Operational Error {e}")
        conn.rollback()
    except ValueError as e:
        print(f"Value Error {e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    init_db()
    trip = get_data()
    noti = generate_notification(trip)
    send(noti)
    save_trip(trip)


if __name__ == "__main__":
    main()