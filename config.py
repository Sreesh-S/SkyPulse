from dotenv import load_dotenv
import os

load_dotenv()

# Try to get API key from Streamlit secrets first (for cloud deployment),
# then fall back to environment variable (for local development)
def _get_api_key():
    try:
        import streamlit as st
        key = st.secrets.get("OPENWEATHER_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("OPENWEATHER_API_KEY")

API_KEY = _get_api_key()
if not API_KEY:
    raise RuntimeError(
        "OPENWEATHER_API_KEY is not set. "
        "For local dev, add it to your .env file. "
        "For Streamlit Cloud, add it under App Settings → Secrets."
    )

BASE_URL = "https://api.openweathermap.org/data/2.5"
WEATHER_URL   = f"{BASE_URL}/weather"
FORECAST_URL  = f"{BASE_URL}/forecast"
AIR_POLLUTION_URL = f"{BASE_URL}/air_pollution"
GEO_REVERSE_URL   = "https://api.openweathermap.org/geo/1.0/reverse"
