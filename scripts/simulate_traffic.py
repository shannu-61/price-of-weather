import pandas as pd
import numpy as np
import os
import sys
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "bigquery_key.json"
)

np.random.seed(42)

BASE_TRAFFIC = {
    "cafe": 150,
    "restaurant": 200,
    "ice_cream_shop": 120,
    "gym": 180,
    "movie_theater": 300,
    "shopping_mall": 2000,
    "park": 500,
    "bar": 250
}

WEATHER_IMPACT = {
    "cafe": {"rainy": -0.10, "cloudy": -0.03, "clear": 0.05, "snowy": -0.25, "extreme_heat": -0.05, "extreme_cold": -0.20},
    "restaurant": {"rainy": -0.15, "cloudy": -0.02, "clear": 0.05, "snowy": -0.30, "extreme_heat": -0.05, "extreme_cold": -0.15},
    "ice_cream_shop": {"rainy": -0.40, "cloudy": -0.15, "clear": 0.20, "snowy": -0.60, "extreme_heat": 0.35, "extreme_cold": -0.50},
    "gym": {"rainy": 0.10, "cloudy": 0.05, "clear": -0.05, "snowy": -0.15, "extreme_heat": 0.10, "extreme_cold": -0.10},
    "movie_theater": {"rainy": 0.25, "cloudy": 0.10, "clear": -0.10, "snowy": -0.20, "extreme_heat": 0.20, "extreme_cold": -0.10},
    "shopping_mall": {"rainy": 0.15, "cloudy": 0.05, "clear": -0.05, "snowy": -0.25, "extreme_heat": 0.15, "extreme_cold": -0.15},
    "park": {"rainy": -0.60, "cloudy": -0.20, "clear": 0.25, "snowy": -0.70, "extreme_heat": -0.30, "extreme_cold": -0.55},
    "bar": {"rainy": -0.05, "cloudy": 0.00, "clear": 0.05, "snowy": -0.20, "extreme_heat": 0.00, "extreme_cold": -0.15}
}

WEEKEND_BOOST = {
    "cafe": 0.20,
    "restaurant": 0.40,
    "ice_cream_shop": 0.50,
    "gym": -0.10,
    "movie_theater": 0.60,
    "shopping_mall": 0.45,
    "park": 0.70,
    "bar": 0.55
}


def get_weather_effect(category, weather_cat, severity):
    impacts = WEATHER_IMPACT.get(category, {})
    effect = impacts.get(weather_cat, 0)
    if severity == "moderate":
        effect *= 1.3
    elif severity == "severe":
        effect *= 1.8
    elif severity in ["extreme_heat", "extreme_cold"]:
        effect = impacts.get(severity, effect)
    return effect


def simulate_daily_traffic(weather_df):
    records = []
    for _, day in weather_df.iterrows():
        for category, base in BASE_TRAFFIC.items():
            traffic = base
            weather_effect = get_weather_effect(
                category,
                day["weather_category"],
                day["weather_severity"]
            )
            traffic *= (1 + weather_effect)
            if day["is_weekend"] == 1:
                traffic *= (1 + WEEKEND_BOOST[category])
            temp = day["temp_avg_f"]
            if 65 <= temp <= 80:
                traffic *= 1.08
            elif temp > 95:
                traffic *= 0.85
            elif temp < 35:
                traffic *= 0.80
            precip = day.get("precip_inches", 0)
            if precip > 1.0:
                traffic *= 0.75
            elif precip > 0.5:
                traffic *= 0.90
            noise = np.random.normal(1.0, 0.15)
            traffic *= max(noise, 0.3)
            base_sentiment = 0.65
            if day["weather_category"] == "clear":
                base_sentiment += 0.10
            elif day["weather_category"] == "rainy":
                base_sentiment -= 0.08
            elif day["weather_category"] == "snowy":
                base_sentiment -= 0.12
            if day["is_weekend"] == 1:
                base_sentiment += 0.05
            sentiment = base_sentiment + np.random.normal(0, 0.08)
            sentiment = max(0, min(1, sentiment))
            records.append({
                "date": day["date"],
                "category": category,
                "estimated_visitors": int(traffic),
                "weather_category": day["weather_category"],
                "weather_severity": day["weather_severity"],
                "temp_avg_f": day["temp_avg_f"],
                "precip_inches": day.get("precip_inches", 0),
                "is_weekend": day["is_weekend"],
                "day_of_week": day["day_of_week"],
                "month_name": day["month_name"],
                "temp_bucket": day["temp_bucket"],
                "sentiment_score": round(sentiment, 3)
            })
    return pd.DataFrame(records)


if __name__ == "__main__":
    print("=" * 50)
    print("  Generating Simulated Foot Traffic Data")
    print("=" * 50)

    weather = pd.read_csv("data/processed/weather_clean.csv")
    weather["date"] = pd.to_datetime(weather["date"])
    print(f"\n  Weather days: {len(weather)}")

    traffic_df = simulate_daily_traffic(weather)
    print(f"  Generated: {len(traffic_df)} records")

    print(f"\n  --- Traffic Summary by Category ---")
    summary = traffic_df.groupby("category")["estimated_visitors"].agg(["mean", "min", "max"]).round(0)
    print(f"\n{summary.to_string()}")

    print(f"\n  --- Weather Impact Preview ---")
    weather_impact = traffic_df.groupby(["weather_category", "category"])["estimated_visitors"].mean().unstack().round(0)
    print(f"\n{weather_impact.to_string()}")

    traffic_df.to_csv("data/processed/daily_traffic.csv", index=False)
    print(f"\n  Saved: data/processed/daily_traffic.csv")

    print("\n  Uploading to BigQuery...")
    client = bigquery.Client(project="price-of-weather")
    table_id = "price-of-weather.weather_impact.daily_traffic"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=True
    )
    job = client.load_table_from_dataframe(traffic_df, table_id, job_config=job_config)
    job.result()
    table = client.get_table(table_id)
    print(f"  Uploaded: {table.num_rows} rows to BigQuery")

    print("\n" + "=" * 50)
    print("  Traffic simulation complete!")
    print("=" * 50)