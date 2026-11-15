import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import numpy as np
import warnings
warnings.filterwarnings("ignore")

sns.set_style("whitegrid")

def load_data():
    traffic = pd.read_csv("data/processed/daily_traffic.csv")
    traffic["date"] = pd.to_datetime(traffic["date"])
    return traffic

def analysis_1_weather_impact(df):
    print("\n" + "=" * 50)
    print("  ANALYSIS 1: Weather Impact by Business Type")
    print("=" * 50)

    pivot = df.groupby(["weather_category", "category"])["estimated_visitors"].mean().unstack().round(0)
    print(f"\n  Average Daily Visitors:\n\n{pivot.to_string()}")

    # Calculate % change from clear days
    print(f"\n  % Change vs Clear Days:\n")
    for cat in pivot.columns:
        clear_val = pivot.loc["clear", cat]
        for weather in ["cloudy", "rainy", "snowy"]:
            if weather in pivot.index:
                val = pivot.loc[weather, cat]
                pct = ((val - clear_val) / clear_val) * 100
                print(f"    {cat:20s} | {weather:8s}: {pct:+.1f}%")
        print()

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: Grouped bar chart
    pivot.plot(kind="bar", ax=axes[0, 0], colormap="Set2", width=0.8)
    axes[0, 0].set_title("Average Visitors by Weather & Business", fontsize=13, fontweight="bold")
    axes[0, 0].set_ylabel("Daily Visitors")
    axes[0, 0].tick_params(axis="x", rotation=45)
    axes[0, 0].legend(fontsize=8, loc="upper right")

    # Plot 2: Heatmap of % change
    pct_change = pivot.copy()
    for col in pct_change.columns:
        clear_val = pct_change.loc["clear", col]
        pct_change[col] = ((pct_change[col] - clear_val) / clear_val) * 100
    sns.heatmap(pct_change, annot=True, fmt=".0f", cmap="RdYlGn", center=0, ax=axes[0, 1])
    axes[0, 1].set_title("% Change in Visitors vs Clear Days", fontsize=13, fontweight="bold")

    # Plot 3: Top winners and losers
    rainy_impact = {}
    for cat in pivot.columns:
        clear_val = pivot.loc["clear", cat]
        rainy_val = pivot.loc["rainy", cat]
        rainy_impact[cat] = ((rainy_val - clear_val) / clear_val) * 100
    rainy_sorted = dict(sorted(rainy_impact.items(), key=lambda x: x[1]))
    colors = ["#e74c3c" if v < 0 else "#2ecc71" for v in rainy_sorted.values()]
    axes[1, 0].barh(list(rainy_sorted.keys()), list(rainy_sorted.values()), color=colors)
    axes[1, 0].set_title("Rainy Day Impact (% Change)", fontsize=13, fontweight="bold")
    axes[1, 0].set_xlabel("% Change in Visitors")
    axes[1, 0].axvline(x=0, color="black", linewidth=0.5)

    # Plot 4: Weekend vs Weekday
    weekend_data = df.groupby(["is_weekend", "category"])["estimated_visitors"].mean().unstack()
    weekend_data.index = ["Weekday", "Weekend"]
    weekend_data.plot(kind="bar", ax=axes[1, 1], colormap="Set2", width=0.8)
    axes[1, 1].set_title("Weekday vs Weekend Visitors", fontsize=13, fontweight="bold")
    axes[1, 1].set_ylabel("Daily Visitors")
    axes[1, 1].tick_params(axis="x", rotation=0)
    axes[1, 1].legend(fontsize=8)

    plt.tight_layout()
    plt.savefig("data/processed/weather_impact_v2.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: data/processed/weather_impact_v2.png")


def analysis_2_statistical_tests(df):
    print("\n" + "=" * 50)
    print("  ANALYSIS 2: Statistical Significance Tests")
    print("=" * 50)

    categories = df["category"].unique()

    print("\n  T-Test: Rainy vs Clear Days (visitors)")
    print("  " + "-" * 65)
    for cat in sorted(categories):
        rainy = df[(df["category"] == cat) & (df["weather_category"] == "rainy")]["estimated_visitors"]
        clear = df[(df["category"] == cat) & (df["weather_category"] == "clear")]["estimated_visitors"]
        t_stat, p_value = stats.ttest_ind(rainy, clear)
        diff_pct = ((rainy.mean() - clear.mean()) / clear.mean()) * 100
        sig = "SIGNIFICANT" if p_value < 0.05 else "Not significant"
        print(f"    {cat:20s} | diff: {diff_pct:+6.1f}% | p={p_value:.6f} | {sig}")

    print("\n  Correlation: Temperature vs Visitors")
    print("  " + "-" * 65)
    for cat in sorted(categories):
        cat_data = df[df["category"] == cat]
        corr, p_value = stats.pearsonr(cat_data["temp_avg_f"], cat_data["estimated_visitors"])
        sig = "SIGNIFICANT" if p_value < 0.05 else "Not significant"
        print(f"    {cat:20s} | r={corr:+.3f} | p={p_value:.6f} | {sig}")

    print("\n  Correlation: Precipitation vs Visitors")
    print("  " + "-" * 65)
    for cat in sorted(categories):
        cat_data = df[df["category"] == cat]
        corr, p_value = stats.pearsonr(cat_data["precip_inches"], cat_data["estimated_visitors"])
        sig = "SIGNIFICANT" if p_value < 0.05 else "Not significant"
        print(f"    {cat:20s} | r={corr:+.3f} | p={p_value:.6f} | {sig}")


def analysis_3_sentiment(df):
    print("\n" + "=" * 50)
    print("  ANALYSIS 3: Customer Sentiment vs Weather")
    print("=" * 50)

    sentiment_by_weather = df.groupby("weather_category")["sentiment_score"].mean().round(3)
    print(f"\n  Average Sentiment by Weather:")
    for weather, score in sentiment_by_weather.items():
        bar = "█" * int(score * 50)
        print(f"    {weather:10s}: {score:.3f} {bar}")

    sentiment_by_cat = df.groupby(["weather_category", "category"])["sentiment_score"].mean().unstack().round(3)
    print(f"\n  Sentiment by Weather & Category:\n\n{sentiment_by_cat.to_string()}")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    sentiment_by_weather.plot(kind="bar", ax=axes[0], color=["#f1c40f", "#95a5a6", "#3498db", "#ecf0f1"])
    axes[0].set_title("Customer Sentiment by Weather", fontsize=13, fontweight="bold")
    axes[0].set_ylabel("Sentiment Score (0-1)")
    axes[0].tick_params(axis="x", rotation=45)

    sns.heatmap(sentiment_by_cat, annot=True, fmt=".3f", cmap="RdYlGn", ax=axes[1])
    axes[1].set_title("Sentiment: Weather x Category", fontsize=13, fontweight="bold")

    plt.tight_layout()
    plt.savefig("data/processed/sentiment_analysis.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n  Saved: data/processed/sentiment_analysis.png")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  PRICE OF WEATHER: Full Analysis v2")
    print("  Dallas, TX | 12-Month Study")
    print("=" * 50)

    df = load_data()
    print(f"\n  Loaded {len(df)} traffic records")

    analysis_1_weather_impact(df)
    analysis_2_statistical_tests(df)
    analysis_3_sentiment(df)

    print("\n" + "=" * 50)
    print("  ALL ANALYSIS COMPLETE!")
    print("=" * 50)