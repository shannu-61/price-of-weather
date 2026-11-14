import requests
import pandas as pd
import json
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.secrets import YELP_API_KEY

LAT = 32.7767
LON = -96.7970

CATEGORIES = {
    "cafe": "coffee",
    "restaurant": "restaurants",
    "ice_cream_shop": "icecream",
    "gym": "gyms",
    "movie_theater": "movietheaters",
    "shopping_mall": "shoppingcenters",
    "park": "parks",
    "bar": "bars"
}

def search_yelp_businesses(category_name, yelp_category):
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {
        "latitude": LAT,
        "longitude": LON,
        "categories": yelp_category,
        "limit": 10,
        "sort_by": "review_count",
        "radius": 15000
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        businesses = []
        for biz in data.get("businesses", []):
            business = {
                "yelp_id": biz["id"],
                "name": biz["name"],
                "category": category_name,
                "rating": biz["rating"],
                "review_count": biz["review_count"],
                "price": biz.get("price", "N/A"),
                "address": ", ".join(biz["location"].get("display_address", [])),
                "lat": biz["coordinates"]["latitude"],
                "lng": biz["coordinates"]["longitude"]
            }
            businesses.append(business)
        return businesses
    else:
        print(f"  Error: {response.status_code} - {response.text}")
        return []

if __name__ == "__main__":
    all_businesses = []
    
    for category_name, yelp_category in CATEGORIES.items():
        print(f"Searching Yelp for {category_name}s in Dallas...")
        businesses = search_yelp_businesses(category_name, yelp_category)
        all_businesses.extend(businesses)
        print(f"  Found {len(businesses)} {category_name}s")
        time.sleep(1)
    
    if all_businesses:
        df = pd.DataFrame(all_businesses)
        
        output_path = "data/raw/yelp_businesses.csv"
        df.to_csv(output_path, index=False)
        
        print(f"\n--- Summary ---")
        print(f"Total businesses: {len(df)}")
        print(f"\nBy category:")
        print(df["category"].value_counts().to_string())
        print(f"\nAvg rating: {df['rating'].mean():.2f}")
        print(f"Avg review count: {df['review_count'].mean():.0f}")
        print(f"\nSaved to {output_path}")
    else:
        print("No businesses found.")