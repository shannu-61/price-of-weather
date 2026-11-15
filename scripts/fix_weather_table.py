import pandas as pd
from google.cloud import bigquery
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "bigquery_key.json"
)

# Re-upload the full 12 months data
client = bigquery.Client(project="price-of-weather")
table_id = "price-of-weather.weather_impact.daily_weather"

df = pd.read_csv("data/raw/dallas_weather_12months.csv")

job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_TRUNCATE",
    autodetect=True
)

job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()

table = client.get_table(table_id)
print(f"Restored! {table.num_rows} rows in daily_weather")