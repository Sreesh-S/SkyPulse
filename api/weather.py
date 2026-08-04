import requests
import urllib3
from config import API_KEY, WEATHER_URL, FORECAST_URL, AIR_POLLUTION_URL, GEO_REVERSE_URL

# Disable SSL warnings if local verification falls back
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _fetch_api(url, params):
    """Helper to perform requests with SSL verification fallback."""
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.SSLError:
        response = requests.get(url, params=params, timeout=10, verify=False)
        response.raise_for_status()
        return response.json()

def get_current_weather(city: str, units: str = "metric"):
    """Fetch current weather data for a city."""
    if not API_KEY:
        raise RuntimeError("OpenWeather API key is not configured in .env.")

    params = {
        "q": city,
        "appid": API_KEY,
        "units": units
    }

    try:
        data = _fetch_api(WEATHER_URL, params)
        return {
            "city": data["name"],
            "country": data["sys"]["country"],
            "coord": data["coord"],
            "temperature": round(data["main"]["temp"], 1),
            "temp_min": round(data["main"]["temp_min"], 1),
            "temp_max": round(data["main"]["temp_max"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"]["speed"],
            "wind_deg": data["wind"].get("deg", 0),
            "wind_gust": data["wind"].get("gust", 0),
            "visibility": round(data.get("visibility", 0) / 1000, 1),
            "weather": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"],
            "clouds": data["clouds"]["all"],
            "sunrise": data["sys"]["sunrise"],
            "sunset": data["sys"]["sunset"],
            "timezone": data.get("timezone", 0)
        }
    except Exception as e:
        print(f"Error fetching current weather: {e}")
        return None

def get_forecast(city: str, units: str = "metric"):
    """Fetch 5-day / 3-hour forecast for a city."""
    if not API_KEY:
        raise RuntimeError("OpenWeather API key is not configured in .env.")

    params = {
        "q": city,
        "appid": API_KEY,
        "units": units
    }

    try:
        data = _fetch_api(FORECAST_URL, params)
        forecast_list = []
        for item in data.get("list", []):
            forecast_list.append({
                "dt": item["dt"],
                "dt_txt": item["dt_txt"],
                "temp": round(item["main"]["temp"], 1),
                "temp_min": round(item["main"]["temp_min"], 1),
                "temp_max": round(item["main"]["temp_max"], 1),
                "feels_like": round(item["main"]["feels_like"], 1),
                "humidity": item["main"]["humidity"],
                "pop": round(item.get("pop", 0) * 100),  # Probability of precipitation %
                "weather": item["weather"][0]["main"],
                "description": item["weather"][0]["description"],
                "icon": item["weather"][0]["icon"],
                "wind_speed": item["wind"]["speed"]
            })

        return {
            "city": data["city"]["name"],
            "country": data["city"]["country"],
            "timezone": data["city"]["timezone"],
            "list": forecast_list
        }
    except Exception as e:
        print(f"Error fetching forecast data: {e}")
        return None

def get_air_quality(lat: float, lon: float):
    """Fetch Air Pollution / AQI data for coordinates."""
    if not API_KEY:
        return None

    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY
    }

    try:
        data = _fetch_api(AIR_POLLUTION_URL, params)
        item = data["list"][0]
        return {
            "aqi": item["main"]["aqi"],
            "components": item["components"]  # pm2_5, pm10, no2, o3, co, so2
        }
    except Exception as e:
        print(f"Error fetching air quality: {e}")
        return None


def get_city_from_coords(lat: float, lon: float) -> str | None:
    """Reverse-geocode lat/lon to a city name using OpenWeatherMap Geo API."""
    if not API_KEY:
        return None
    params = {"lat": lat, "lon": lon, "limit": 1, "appid": API_KEY}
    try:
        data = _fetch_api(GEO_REVERSE_URL, params)
        if data and isinstance(data, list) and data[0].get("name"):
            return data[0]["name"]
    except Exception as e:
        print(f"Error reverse-geocoding coordinates: {e}")
    return None