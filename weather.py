import json

from load_location import get_env
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta





OPEN_WEATHER_API = get_env("OPEN_WEATHER_API")

def current_weather(lat, lon, units = "metric"):
    OPEN_WEATHER_URL = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPEN_WEATHER_API}&units={units}"

    open_weather = requests.get(OPEN_WEATHER_URL,timeout = 120)

    data = open_weather.json()

    with open("test" , mode='w') as f:
        json.dump(data, f,ensure_ascii=False, indent= 2)

    main_weather = data["weather"][0]["main"]
    dt = data["dt"]
    offset = data["timezone"]
    clouds_perc = data["clouds"]["all"]
    wind = data["wind"]["speed"]
    location = data["name"]
    data_df = pd.DataFrame([data["main"]])

    utc = datetime.fromtimestamp(dt, tz= timezone.utc)
    tz = timezone(timedelta(seconds = offset))
    local_time = utc.astimezone(tz)

    temp = data_df["temp"]
    temp_feels_like = data_df["feels_like"]

    return pd.DataFrame({
        "location" : location,
        "local_time" : local_time,
        "main" : main_weather,
        "temp" : temp,
        "feels_like" : temp_feels_like,
        "wind" : wind,
        "clouds_percentage" : clouds_perc
    })

