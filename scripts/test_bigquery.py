import os
import sys
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "bigquery_key.json"
)

client = bigquery.Client(project="price-of-weather")

# Query 1: Rainiest days in Dallas
print("=== Top 10 Rainiest Days in Dallas ===\n")
query1 = """
SELECT date, temp_avg_f, precip_inches, condition, description
FROM `price-of-weather.weather_impact.daily_weather`
WHERE precip_inches > 0
ORDER BY precip_inches DESC
LIMIT 10
"""
for row in client.query(query1):
    print(f"  {row.date} | {row.temp_avg_f}°F | {row.precip_inches}in rain | {row.condition}")

# Query 2: Business count by category
print("\n=== Google Businesses by Category ===\n")
query2 = """
SELECT category, COUNT(*) as count, ROUND(AVG(rating), 2) as avg_rating
FROM `price-of-weather.weather_impact.google_businesses`
GROUP BY category
ORDER BY avg_rating DESC
"""
for row in client.query(query2):
    print(f"  {row.category}: {row.count} businesses, avg rating {row.avg_rating}")

# Query 3: Yelp most reviewed businesses
print("\n=== Top 5 Most Reviewed on Yelp ===\n")
query3 = """
SELECT name, category, rating, review_count
FROM `price-of-weather.weather_impact.yelp_businesses`
ORDER BY review_count DESC
LIMIT 5
"""
for row in client.query(query3):
    print(f"  {row.name} ({row.category}) - {row.rating}★ ({row.review_count} reviews)")