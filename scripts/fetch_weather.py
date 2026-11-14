import requests
import json
import os
from datetime import datetime

# Add the project root to path so we can import config
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.secrets import OPENWEATHER_API_KEY

# Dallas coordinates
LAT = 32.7767
LON = -96.7970

def fetch_current_weather():
    """Fetch current weather for Dallas"""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": LAT,
        "lon": LON,
        "appid": OPENWEATHER_API_KEY,
        "units": "imperial"  # Fahrenheit
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        weather = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "city": "Dallas",
            "temp_f": data["main"]["temp"],
            "feels_like_f": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "condition": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "wind_speed_mph": data["wind"]["speed"],
            "clouds_pct": data["clouds"]["all"]
        }
        return weather
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    print("Fetching Dallas weather data...")
    result = fetch_current_weather()

    if result:
        print("\n--- Dallas Weather Right Now ---")
        for key, value in result.items():
            print(f"  {key}: {value}")

        # Save to raw data folder
        filename = f"data/raw/weather_{result['date']}.json"
        with open(filename, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved to {filename}")
    else:
        print("Failed to fetch weather data.")