# MevoInformator

Skrypt w Pythonie, który pomaga zdecydować, czy dojechać do celu rowerem miejskim Mevo, czy samochodem. Przy każdym uruchomieniu sprawdza dostępność rowerów elektrycznych na stacji startowej i wolnych stojaków przy celu, pobiera pogodę w obu miejscach, porównuje czas przejazdu rowerem i autem, wysyła podsumowanie jako powiadomienie push i zapisuje wynik do bazy SQLite. Z czasem powstaje historia przejazdów wraz z pogodą i ruchem, którą można wykorzystać do analizy lub uczenia modeli ML.

## Jak to działa

1. **Sprawdzenie limitów API** – przed startem skrypt liczy wcześniejsze wywołania zapisane w `api_logs.db` i przerywa działanie, jeśli któreś API przekroczyło limit (domyślnie 50).
2. **Dane o stacjach Mevo** – z publicznego feedu GBFS (`gbfs.urbansharing.com/rowermevo.pl`) pobierane są lista stacji i ich aktualny status.
3. **Stacja startowa** – wskazana współrzędnymi w konfiguracji. Musi być zainstalowana, wypożyczać rowery i mieć co najmniej jeden rower elektryczny.
4. **Stacja docelowa** – najbliższa stacja w promieniu 400 m od punktu docelowego, która przyjmuje zwroty i ma co najmniej jeden wolny stojak.
5. **Pogoda** – aktualne warunki dla punktu startowego i docelowego z OpenWeather (stan, temperatura, temperatura odczuwalna, wiatr, zachmurzenie).
6. **Czasy przejazdu** – Mapbox Directions: trasa rowerem (`cycling`) oraz samochodem (`driving-traffic`) z typowym czasem przejazdu w ruchu.
7. **Powiadomienie** – podsumowanie (po polsku) trafia na serwer [ntfy](https://ntfy.sh) w sieci lokalnej.
8. **Zapis do bazy** – wynik jest dopisywany do tabeli `trips` w SQLite.

## Struktura projektu

| Plik / katalog | Rola |
|---|---|
| `main.py` | Punkt wejścia: kontrola limitów API, pobranie danych, wysłanie powiadomienia, zapis do bazy. |
| `apis.py` | Główna logika: pobieranie danych Mevo, wybór stacji startowej i docelowej, składanie wyniku w jeden wiersz `DataFrame`. |
| `weather.py` | Klient OpenWeather (`current_weather`). |
| `directions.py` | Klient Mapbox Directions (`get_travel_duration`) dla roweru i samochodu. |
| `log_api.py` | Rejestr wywołań zewnętrznych API w SQLite (`api_logs.db`). |
| `helpers/` | Funkcje pomocnicze: odległość haversine, wczytywanie konfiguracji (`get_env`), wyjątek `ApiLimitExceededError`. |
| `other/` | Pliki baz danych SQLite (`trips.db`, `api_logs.db`). |

## Konfiguracja

Dane konfiguracyjne i klucze API odczytywane są przez `get_env` ze zmiennych środowiskowych:

| Zmienna | Opis |
|---|---|
| `MEVO_START_LOCATION_LAT`, `MEVO_START_LOCATION_LON` | współrzędne stacji startowej Mevo (muszą dokładnie odpowiadać wpisowi w feedzie GBFS) |
| `CAR_START_LOCATION_LAT`, `CAR_START_LOCATION_LON` | punkt startowy trasy samochodowej |
| `DEST_LOCATION_LAT`, `DEST_LOCATION_LON` | punkt docelowy |
| `MAPBOX_API` | klucz API Mapbox |
| `OPEN_WEATHER_API` | klucz API OpenWeather |
| `SERVER` | nazwa hosta serwera ntfy (adres `http://<SERVER>.local/mevo-updates`) |
| `NTFY_USER`, `NTFY_PASS` | dane logowania do ntfy |

Klucze i hasła nie powinny trafiać do repozytorium (np. trzymaj je w pliku `.env` dodanym do `.gitignore`).

## Wymagania i uruchomienie

- Python 3.9+
- pakiety: `pandas`, `numpy`, `requests`

```bash
pip install pandas numpy requests
python main.py
```

Skrypt wykonuje jeden pomiar na uruchomienie, więc do regularnego działania najlepiej uruchamiać go z harmonogramu (np. `cron`) o stałych porach, na przykład rano przed wyjściem.

## Dane wyjściowe

Każdy przebieg dopisuje wiersz do tabeli `trips` (`other/trips.db`) z kolumnami:

| Grupa | Kolumny |
|---|---|
| Stacje | `start_station`, `start_station_address`, `available_ebikes`, `closest_dest_station`, `dest_station_address`, `docks_available` |
| Pogoda na starcie | `start_location_weather`, `start_location_weather_time`, `start_weather_status`, `start_temp`, `start_temp_feels_like`, `start_wind_ms`, `start_clouds_perc` |
| Pogoda w celu | `dest_location_weather`, `dest_location_weather_time`, `dest_weather_status`, `dest_temp`, `dest_temp_feels_like`, `dest_wind_ms`, `dest_clouds_perc` |
| Rower | `bike_travel_duration_min`, `bike_distance_km` |
| Samochód | `car_travel_duration_min`, `car_travel_duration_min_typical`, `car_distance_km` |
| Metadane | `id`, `call_date` |

Przykładowa treść powiadomienia zawiera: stację początkową i liczbę e-rowerów, stację końcową i liczbę wolnych stojaków, pogodę w obu miejscach oraz czas i dystans dla roweru i samochodu.

## Ograniczenia i plany

- Czas przejazdu samochodem jest liczony dla stałej godziny wyjazdu (domyślnie 7:20 bieżącego dnia), a nie dla chwili uruchomienia skryptu.
- Limit zapytań do API liczy wszystkie zapisane wywołania, bez podziału na dni.
- Stacja startowa jest stała (jedna para współrzędnych), a stacja docelowa wybierana automatycznie.
- Brak testów automatycznych.
