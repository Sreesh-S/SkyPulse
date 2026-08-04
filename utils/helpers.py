from datetime import datetime, timezone, timedelta

def get_unit_symbols(unit_system: str):
    """Return unit labels based on metric or imperial choice."""
    if unit_system == "imperial":
        return {
            "temp": "°F",
            "speed": "mph",
            "pressure": "inHg"
        }
    return {
        "temp": "°C",
        "speed": "m/s",
        "pressure": "hPa"
    }

def deg_to_compass(num):
    """Convert wind degree to compass direction."""
    val = int((num / 22.5) + .5)
    arr = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return arr[(val % 16)]

def get_aqi_info(aqi: int):
    """Return exact mandatory AQI label, color code, and description."""
    aqi_dict = {
        1: {
            "label": "Excellent",
            "color": "#22C55E",
            "bg": "rgba(34, 197, 94, 0.15)",
            "desc": "Air quality is ideal for outdoor activities; no health risk."
        },
        2: {
            "label": "Good",
            "color": "#84CC16",
            "bg": "rgba(132, 204, 22, 0.15)",
            "desc": "Air quality is acceptable; minor concern for extremely sensitive individuals."
        },
        3: {
            "label": "Moderate",
            "color": "#EAB308",
            "bg": "rgba(234, 179, 8, 0.15)",
            "desc": "Sensitive groups may experience health symptoms."
        },
        4: {
            "label": "Poor",
            "color": "#F97316",
            "bg": "rgba(249, 115, 22, 0.15)",
            "desc": "Unhealthy for sensitive individuals; general public may feel discomfort."
        },
        5: {
            "label": "Very Poor",
            "color": "#EF4444",
            "bg": "rgba(239, 68, 68, 0.15)",
            "desc": "Health alert: serious risk of health effects for everyone."
        }
    }
    return aqi_dict.get(aqi, {
        "label": "Hazardous",
        "color": "#991B1B",
        "bg": "rgba(153, 27, 27, 0.2)",
        "desc": "Emergency health advisory: severe conditions."
    })

def get_weather_color(weather_main: str):
    """Return mandatory weather color accent."""
    w = weather_main.lower()
    if "sun" in w or "clear" in w:
        return "#FACC15"
    elif "cloud" in w:
        return "#94A3B8"
    elif "heavy" in w and "rain" in w:
        return "#2563EB"
    elif "rain" in w or "drizzle" in w:
        return "#3B82F6"
    elif "thunder" in w or "lightning" in w:
        return "#7C3AED"
    elif "snow" in w:
        return "#E2E8F0"
    elif "fog" in w or "mist" in w or "haze" in w:
        return "#CBD5E1"
    elif "wind" in w:
        return "#38BDF8"
    return "#3B82F6"

def format_timestamp(ts: int, tz_offset_seconds: int = 0, fmt: str = "%H:%M"):
    """Format Unix timestamp with city timezone offset."""
    tz = timezone(timedelta(seconds=tz_offset_seconds))
    dt = datetime.fromtimestamp(ts, tz=tz)
    return dt.strftime(fmt)

def group_forecast_by_day(forecast_list):
    """Group 3-hour forecast items by calendar day."""
    days = {}
    for item in forecast_list:
        date_str = item["dt_txt"].split(" ")[0]
        if date_str not in days:
            days[date_str] = []
        days[date_str].append(item)

    daily_summary = []
    for date_str, items in days.items():
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        temps = [x["temp"] for x in items]
        pops = [x["pop"] for x in items]
        mid_item = next((x for x in items if "12:00:00" in x["dt_txt"]), items[len(items)//2])
        
        daily_summary.append({
            "date": date_str,
            "day_name": dt_obj.strftime("%a"),
            "full_date": dt_obj.strftime("%b %d"),
            "temp_min": round(min(temps), 1),
            "temp_max": round(max(temps), 1),
            "pop_max": max(pops),
            "weather": mid_item["weather"],
            "description": mid_item["description"],
            "icon": mid_item["icon"]
        })

    return daily_summary
