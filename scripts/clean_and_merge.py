import pandas as pd
import os
import sys
from google.cloud import bigquery
from textblob import TextBlob

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "bigquery_key.json"
)

PROJECT_ID = "price-of-weather"
client = bigquery.Client(project=PROJECT_ID)


def load_from_bigquery(table_name):
    query = f"SELECT * FROM `{PROJECT_ID}.weather_impact.{table_name}`"
    return client.query(query).to_dataframe()


def clean_weather(df):
    """Clean and add features to weather data"""
    print("Cleaning weather data...")
    
    # Convert date to datetime
    df["date"] = pd.to_datetime(df["date"])
    
    # Fill missing values
    df["precip_inches"] = df["precip_inches"].fillna(0)
    df["snow_inches"] = df["snow_inches"].fillna(0)
    
    # Add time features
    df["day_of_week"] = df["date"].dt.day_name()
    df["is_weekend"] = df["date"].dt.dayofweek.isin([5, 6]).astype(int)
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.month_name()
    
    # Add weather severity
    def weather_severity(row):
        if row["snow_inches"] > 0:
            return "severe"
        elif row["precip_inches"] > 0.5:
            return "moderate"
        elif row["precip_inches"] > 0:
            return "mild"
        elif row["temp_max_f"] > 100:
            return "extreme_heat"
        elif row["temp_min_f"] < 32:
            return "extreme_cold"
        else:
            return "normal"
    
    df["weather_severity"] = df.apply(weather_severity, axis=1)
    
    # Add weather category (simplified)
    def weather_category(condition):
        condition = str(condition).lower()
        if "rain" in condition or "shower" in condition:
            return "rainy"
        elif "snow" in condition or "ice" in condition:
            return "snowy"
        elif "cloud" in condition or "overcast" in condition:
            return "cloudy"
        elif "clear" in condition or "sunny" in condition:
            return "clear"
        else:
            return "other"
    
    df["weather_category"] = df["condition"].apply(weather_category)
    
    # Temperature bins
    df["temp_bucket"] = pd.cut(
        df["temp_avg_f"],
        bins=[0, 32, 50, 65, 80, 95, 120],
        labels=["freezing", "cold", "cool", "warm", "hot", "extreme_hot"]
    )
    
    print(f"  ✓ {len(df)} rows, {len(df.columns)} columns")
    print(f"  Weather categories: {df['weather_category'].value_counts().to_dict()}")
    print(f"  Severity: {df['weather_severity'].value_counts().to_dict()}")
    return df


def clean_businesses(google_df, yelp_df):
    """Clean and merge business data"""
    print("\nCleaning business data...")
    
    # Standardize Google data
    google_df = google_df.rename(columns={"total_ratings": "review_count"})
    google_df["source"] = "google"
    
    # Standardize Yelp data
    yelp_df["source"] = "yelp"
    yelp_df = yelp_df.rename(columns={"yelp_id": "place_id"})
    
    # Keep common columns
    common_cols = ["place_id", "name", "category", "rating", "review_count",
                   "address", "lat", "lng", "source"]
    
    google_clean = google_df[[c for c in common_cols if c in google_df.columns]]
    yelp_clean = yelp_df[[c for c in common_cols if c in yelp_df.columns]]
    
    # Combine
    all_businesses = pd.concat([google_clean, yelp_clean], ignore_index=True)
    
    # Remove duplicates (same name + category)
    all_businesses = all_businesses.drop_duplicates(
        subset=["name", "category"], keep="first"
    )
    
    # Add rating tier
    def rating_tier(rating):
        if rating is None:
            return "unknown"
        elif rating >= 4.5:
            return "excellent"
        elif rating >= 4.0:
            return "good"
        elif rating >= 3.5:
            return "average"
        else:
            return "below_average"
    
    all_businesses["rating_tier"] = all_businesses["rating"].apply(rating_tier)
    
    print(f"  ✓ {len(all_businesses)} unique businesses")
    print(f"  By category: {all_businesses['category'].value_counts().to_dict()}")
    print(f"  By source: {all_businesses['source'].value_counts().to_dict()}")
    return all_businesses


def create_analysis_table(weather_df, business_df):
    """Create a cross-join table for analysis: every business x every weather day"""
    print("\nCreating analysis table...")
    
    # Create a key for cross join
    weather_df["key"] = 1
    business_df["key"] = 1
    
    # Cross join (every business paired with every weather day)
    # But limit to category-level aggregation to keep it manageable
    category_stats = business_df.groupby("category").agg(
        num_businesses=("name", "count"),
        avg_rating=("rating", "mean"),
        avg_review_count=("review_count", "mean")
    ).reset_index()
    
    category_stats["key"] = 1
    
    analysis = weather_df.merge(category_stats, on="key").drop("key", axis=1)
    
    print(f"  ✓ {len(analysis)} rows (weather days x categories)")
    print(f"  Columns: {list(analysis.columns)}")
    return analysis


if __name__ == "__main__":
    print("=" * 50)
    print("  Data Cleaning & Feature Engineering")
    print("=" * 50)
    
    # Load data from BigQuery
    print("\nLoading data from BigQuery...")
    weather_raw = load_from_bigquery("daily_weather")
    google_raw = load_from_bigquery("google_businesses")
    yelp_raw = load_from_bigquery("yelp_businesses")
    print(f"  Loaded: {len(weather_raw)} weather, {len(google_raw)} google, {len(yelp_raw)} yelp")
    
    # Clean data
    weather_clean = clean_weather(weather_raw)
    business_clean = clean_businesses(google_raw, yelp_raw)
    analysis_table = create_analysis_table(weather_clean, business_clean)
    
    # Save locally
    weather_clean.to_csv("data/processed/weather_clean.csv", index=False)
    business_clean.to_csv("data/processed/business_clean.csv", index=False)
    analysis_table.to_csv("data/processed/analysis_table.csv", index=False)
    
    # Upload cleaned data to BigQuery
    print("\nUploading cleaned data to BigQuery...")
    for df, name in [(weather_clean, "weather_clean"),
                     (business_clean, "business_clean"),
                     (analysis_table, "analysis_table")]:
        table_id = f"{PROJECT_ID}.weather_impact.{name}"
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            autodetect=True
        )
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        table = client.get_table(table_id)
        print(f"  ✓ {name}: {table.num_rows} rows")
    
    print("\n" + "=" * 50)
    print("  Cleaning complete!")
    print("=" * 50)