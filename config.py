from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENWEATHER_API_KEY is not set in .env. Please add it and restart the app.")

BASE_URL = "https://api.openweathermap.org/data/2.5"
WEATHER_URL   = f"{BASE_URL}/weather"
FORECAST_URL  = f"{BASE_URL}/forecast"
AIR_POLLUTION_URL = f"{BASE_URL}/air_pollution"
GEO_REVERSE_URL   = "https://api.openweathermap.org/geo/1.0/reverse"
