import pandas as pd
from google.cloud import bigquery
import os
import sys

# Set the path to your service account key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "bigquery_key.json"
)

# Your project and dataset
PROJECT_ID = "price-of-weather"
DATASET_ID = "weather_impact"

def upload_to_bigquery(csv_path, table_name):
    """Upload a CSV file to BigQuery"""
    
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    # Read CSV
    df = pd.read_csv(csv_path)
    print(f"\nUploading {table_name}: {len(df)} rows, {len(df.columns)} columns")
    print(f"  Columns: {list(df.columns)}")
    
    # Configure the upload
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Replace table if exists
        autodetect=True  # Auto-detect schema
    )
    
    # Upload
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion
    
    # Verify
    table = client.get_table(table_id)
    print(f"  ✓ Uploaded! {table.num_rows} rows in {table_id}")

if __name__ == "__main__":
    print("=== Uploading data to BigQuery ===\n")
    
    # Upload weather data
    upload_to_bigquery(
        "data/raw/dallas_weather_12months.csv",
        "daily_weather"
    )
    
    # Upload Google Places businesses
    upload_to_bigquery(
        "data/raw/dallas_businesses.csv",
        "google_businesses"
    )
    
    # Upload Yelp businesses
    upload_to_bigquery(
        "data/raw/yelp_businesses.csv",
        "yelp_businesses"
    )
    
    print("\n=== All uploads complete! ===")
    print(f"\nView your data at:")
    print(f"https://console.cloud.google.com/bigquery?project={PROJECT_ID}")