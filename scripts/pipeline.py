from prefect import flow, task
import pandas as pd
import requests
import json
import os
import sys
from datetime import datetime
from google.cloud import bigquery

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.secrets import VISUAL_CROSSING_API_KEY, GOOGLE_PLACES_API_KEY, YELP_API_KEY

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "bigquery_key.json"
)

PROJECT_ID = "price-of-weather"
DATASET_ID = "weather_impact"
LAT = 32.7767
LON = -96.7970


@task(name="Fetch Today's Weather")
def fetch_todays_weather():
    today = datetime.now().strftime("%Y-%m-%d")
    url = (
        f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
        f"Dallas,TX/{today}/{today}"
    )
    params = {
        "unitGroup": "us",
        "key": VISUAL_CROSSING_API_KEY,
        "contentType": "json",
        "include": "days"
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        day = response.json()["days"][0]
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
        print(f"  Weather: {record['temp_avg_f']}°F, {record['condition']}")
        return pd.DataFrame([record])
    else:
        print(f"  Error: {response.status_code}")
        return None


@task(name="Fetch Google Businesses")
def fetch_google_businesses():
    categories = {
        "cafe": "cafe", "restaurant": "restaurant",
        "ice_cream_shop": "ice_cream_shop", "gym": "gym",
        "movie_theater": "movie_theater", "shopping_mall": "shopping_mall",
        "park": "park", "bar": "bar"
    }

    all_businesses = []
    for cat_name, cat_type in categories.items():
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
            "X-Goog-FieldMask": "places.id,places.displayName,places.rating,places.userRatingCount,places.formattedAddress,places.location,places.priceLevel"
        }
        body = {
            "includedTypes": [cat_type],
            "maxResultCount": 10,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": LAT, "longitude": LON},
                    "radius": 15000.0
                }
            }
        }
        response = requests.post(url, headers=headers, json=body)
        if response.status_code == 200:
            data = response.json()
            for place in data.get("places", []):
                all_businesses.append({
                    "place_id": place.get("id", ""),
                    "name": place.get("displayName", {}).get("text", ""),
                    "category": cat_name,
                    "rating": place.get("rating"),
                    "total_ratings": place.get("userRatingCount", 0),
                    "address": place.get("formattedAddress", ""),
                    "lat": place.get("location", {}).get("latitude"),
                    "lng": place.get("location", {}).get("longitude"),
                    "price_level": place.get("priceLevel")
                })

    print(f"  Google: {len(all_businesses)} businesses")
    return pd.DataFrame(all_businesses)


@task(name="Fetch Yelp Businesses")
def fetch_yelp_businesses():
    categories = {
        "cafe": "coffee", "restaurant": "restaurants",
        "ice_cream_shop": "icecream", "gym": "gyms",
        "movie_theater": "movietheaters", "shopping_mall": "shoppingcenters",
        "park": "parks", "bar": "bars"
    }

    all_businesses = []
    for cat_name, yelp_cat in categories.items():
        url = "https://api.yelp.com/v3/businesses/search"
        headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
        params = {
            "latitude": LAT, "longitude": LON,
            "categories": yelp_cat, "limit": 10,
            "sort_by": "review_count", "radius": 15000
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            for biz in response.json().get("businesses", []):
                all_businesses.append({
                    "yelp_id": biz["id"],
                    "name": biz["name"],
                    "category": cat_name,
                    "rating": biz["rating"],
                    "review_count": biz["review_count"],
                    "price": biz.get("price", "N/A"),
                    "address": ", ".join(biz["location"].get("display_address", [])),
                    "lat": biz["coordinates"]["latitude"],
                    "lng": biz["coordinates"]["longitude"]
                })

    print(f"  Yelp: {len(all_businesses)} businesses")
    return pd.DataFrame(all_businesses)


@task(name="Upload to BigQuery")
def upload_to_bigquery(df, table_name):
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=True
    )

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()

    table = client.get_table(table_id)
    print(f"  ✓ {table_name}: {table.num_rows} rows uploaded")


@flow(name="Price of Weather Pipeline")
def weather_pipeline():
    print(f"\n{'='*50}")
    print(f"  Price of Weather Pipeline")
    print(f"  Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # Step 1: Fetch data
    print("Step 1: Fetching data...")
    weather_df = fetch_todays_weather()
    google_df = fetch_google_businesses()
    yelp_df = fetch_yelp_businesses()

    # Step 2: Upload to BigQuery
    print("\nStep 2: Uploading to BigQuery...")
    if weather_df is not None:
        upload_to_bigquery(weather_df, "daily_weather")
    upload_to_bigquery(google_df, "google_businesses")
    upload_to_bigquery(yelp_df, "yelp_businesses")

    print(f"\n{'='*50}")
    print("  Pipeline complete!")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    weather_pipeline()