import sqlite3

def _init_db():
    conn = sqlite3.connect("other/api_logs.db")
    cursor = conn.cursor()
    cursor.execute("""
               CREATE TABLE IF NOT EXISTS apis (
                   event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                   api TEXT,
                   lat_start REAL,
                   lon_start REAL,
                   lat_dest REAL,
                   lon_dest REAL,
                   created_at TEXT DEFAULT CURRENT_TIMESTAMP
               );
           """)
    conn.commit()


def log_api(api : str, lat_start : float, lon_start : float, lat_dest : float, lon_dest : float):
    api = api.lower()
    if api not in ("openweather", "mevo_stations", "mapbox", "mevo_bikes"):
        raise RuntimeError("Wrong api type")


    conn = sqlite3.connect("other/api_logs.db")
    cursor = conn.cursor()

    try:
        if api == "openweather":
            cursor.execute("""INSERT INTO apis (api, lat_start, lon_start, lat_dest, lon_dest) VALUES (?, ?, ?, ?, ?)""",
                           [api, lat_start, lon_start, None, None])
        else:
            cursor.execute("""INSERT INTO apis (api, lat_start, lon_start, lat_dest, lon_dest) VALUES (?, ?, ?, ?, ?)""",
                   [api, lat_start, lon_start, lat_dest, lon_dest])
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


