import pandas as pd
from google.cloud import bigquery
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "config/bigquery_key.json"
client = bigquery.Client()

print("Exporting data for Power BI...")

# Table 1: Daily weather (clean)
query1 = "SELECT * FROM `price-of-weather.weather_impact.weather_clean`"
df1 = client.query(query1).to_dataframe()
df1.to_csv("data/processed/powerbi_weather.csv", index=False)
print(f"  weather: {len(df1)} rows")

# Table 2: Business info
query2 = "SELECT * FROM `price-of-weather.weather_impact.business_clean`"
df2 = client.query(query2).to_dataframe()
df2.to_csv("data/processed/powerbi_businesses.csv", index=False)
print(f"  businesses: {len(df2)} rows")

# Table 3: Daily traffic (the main analysis table)
query3 = "SELECT * FROM `price-of-weather.weather_impact.daily_traffic`"
df3 = client.query(query3).to_dataframe()
df3.to_csv("data/processed/powerbi_traffic.csv", index=False)
print(f"  traffic: {len(df3)} rows")

print("\nAll 3 files saved to data/processed/")
print("Ready for Power BI!")