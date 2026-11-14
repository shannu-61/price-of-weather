import requests
import pandas as pd
import json
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.secrets import GOOGLE_PLACES_API_KEY

# Dallas coordinates
LAT = 32.7767
LON = -96.7970

# Business categories we want to analyze
CATEGORIES = {
    "cafe": "cafe",
    "restaurant": "restaurant",
    "ice_cream_shop": "ice_cream_shop",
    "gym": "gym",
    "movie_theater": "movie_theater",
    "shopping_mall": "shopping_mall",
    "park": "park",
    "bar": "bar"
}

def search_businesses(category_name, category_type):
    """Search for businesses using Places API (New)"""
    
    url = "https://places.googleapis.com/v1/places:searchNearby"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.rating,places.userRatingCount,places.formattedAddress,places.location,places.priceLevel,places.currentOpeningHours"
    }
    
    body = {
        "includedTypes": [category_type],
        "maxResultCount": 10,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": LAT,
                    "longitude": LON
                },
                "radius": 15000.0
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=body)
    
    if response.status_code == 200:
        data = response.json()
        
        if "places" not in data:
            print(f"  No results found")
            return []
        
        businesses = []
        for place in data["places"]:
            business = {
                "place_id": place.get("id", ""),
                "name": place.get("displayName", {}).get("text", ""),
                "category": category_name,
                "rating": place.get("rating", None),
                "total_ratings": place.get("userRatingCount", 0),
                "address": place.get("formattedAddress", ""),
                "lat": place.get("location", {}).get("latitude", None),
                "lng": place.get("location", {}).get("longitude", None),
                "price_level": place.get("priceLevel", None)
            }
            businesses.append(business)
        
        return businesses
    else:
        print(f"  Error: {response.status_code} - {response.text}")
        return []

if __name__ == "__main__":
    all_businesses = []
    
    for category_name, category_type in CATEGORIES.items():
        print(f"Searching for {category_name}s in Dallas...")
        results = search_businesses(category_name, category_type)
        all_businesses.extend(results)
        print(f"  Found {len(results)} {category_name}s")
        time.sleep(2)
    
    if all_businesses:
        df = pd.DataFrame(all_businesses)
        
        output_path = "data/raw/dallas_businesses.csv"
        df.to_csv(output_path, index=False)
        
        json_path = "data/raw/dallas_businesses.json"
        with open(json_path, "w") as f:
            json.dump(all_businesses, f, indent=2)
        
        print(f"\n--- Summary ---")
        print(f"Total businesses: {len(df)}")
        print(f"\nBy category:")
        print(df["category"].value_counts().to_string())
        print(f"\nAvg rating: {df['rating'].mean():.2f}")
        print(f"\nSaved to {output_path}")
    else:
        print("No businesses found.")