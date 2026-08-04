import json
import pandas as pd

def generate_json_export(current_weather, forecast_data, aqi_data):
    """Generate structured JSON payload for download."""
    export_payload = {
        "export_date_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "current_weather": current_weather,
        "air_quality": aqi_data,
        "forecast": forecast_data.get("list", []) if forecast_data else []
    }
    return json.dumps(export_payload, indent=2)

def generate_csv_export(forecast_data):
    """Generate CSV string of forecast data."""
    if not forecast_data or "list" not in forecast_data:
        return ""
    
    df = pd.DataFrame(forecast_data["list"])
    return df.to_csv(index=False)
