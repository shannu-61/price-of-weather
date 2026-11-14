import requests
import pandas as pd
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.secrets import VISUAL_CROSSING_API_KEY

def fetch_historical_weather(start_date, end_date):
    """Fetch historical weather for Dallas from Visual Crossing"""
    
    city = "Dallas,TX"
    url = (
        f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
        f"{city}/{start_date}/{end_date}"
    )
    
    params = {
        "unitGroup": "us",  # Fahrenheit
        "key": VISUAL_CROSSING_API_KEY,
        "contentType": "json",
        "include": "days"
    }
    
    print(f"Fetching weather from {start_date} to {end_date}...")
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        days = data["days"]
        
        records = []
        for day in days:
            record = {
                "date": day["datetime"],
                "city": "Dallas",
                "temp_max_f": day.get("tempmax"),
                "temp_min_f": day.get("tempmin"),
                "temp_avg_f": day.get("temp"),
                "feels_like_f": day.get("feelslike"),
                "humidity": day.get("humidity"),
                "precip_inches": day.get("precip", 0),
                "snow_inches": day.get("snow", 0),
                "wind_speed_mph": day.get("windspeed"),
                "clouds_pct": day.get("cloudcover"),
                "condition": day.get("conditions"),
                "description": day.get("description")
            }
            records.append(record)
        
        return records
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    # Fetch last 12 months of data in chunks (API limit)
    all_records = []
    
    # Define date ranges (3-month chunks)
    date_ranges = [
        ("2025-11-14", "2026-02-13"),
        ("2026-02-14", "2026-05-13"),
        ("2026-05-14", "2026-08-13"),
        ("2026-08-14", "2026-11-14")
    ]
    
    for start, end in date_ranges:
        records = fetch_historical_weather(start, end)
        if records:
            all_records.extend(records)
            print(f"  Got {len(records)} days")
        time.sleep(2)  # Be nice to the API
    
    if all_records:
        df = pd.DataFrame(all_records)
        
        # Save to CSV
        output_path = "data/raw/dallas_weather_12months.csv"
        df.to_csv(output_path, index=False)
        
        print(f"\n--- Summary ---")
        print(f"Total days collected: {len(df)}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"Avg temperature: {df['temp_avg_f'].mean():.1f}°F")
        print(f"Rainy days: {len(df[df['precip_inches'] > 0])}")
        print(f"Snowy days: {len(df[df['snow_inches'] > 0])}")
        print(f"\nSaved to {output_path}")
    else:
        print("Failed to fetch data.")