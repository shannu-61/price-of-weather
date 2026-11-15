import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

def load_data():
    df = pd.read_csv("data/processed/daily_traffic.csv")
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.dayofweek
    return df

def train_per_category(df):
    print("\n" + "=" * 50)
    print("  MODEL RESULTS (Per Category)")
    print("=" * 50)

    weather_features = ["temp_avg_f", "precip_inches", "weather_severity",
                        "is_weekend", "month", "day_of_week"]

    all_results = {}
    all_models = {}

    categories = sorted(df["category"].unique())

    for cat in categories:
        cat_data = df[df["category"] == cat].copy()

        # Add weather dummies
        cat_encoded = pd.get_dummies(cat_data[["weather_category"]], drop_first=True)
        X = pd.concat([cat_data[weather_features], cat_encoded], axis=1)
        X = X.select_dtypes(include=[np.number])
        y = cat_data["estimated_visitors"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42)

        # Train Random Forest
        model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)

        all_results[cat] = {
            "RMSE": rmse, "R2": r2, "MAE": mae,
            "y_test": y_test, "y_pred": y_pred,
            "features": list(X.columns),
            "importances": model.feature_importances_
        }
        all_models[cat] = model

        status = "GREAT" if r2 > 0.7 else "GOOD" if r2 > 0.5 else "OK" if r2 > 0.3 else "LOW"
        print(f"\n  {cat:20s} | R2: {r2:.3f} ({r2*100:.1f}%) | RMSE: {rmse:.0f} | {status}")

    return all_results, all_models

def plot_results(all_results):
    categories = list(all_results.keys())
    r2_scores = [all_results[c]["R2"] for c in categories]

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: R2 by category
    colors = ["#2ecc71" if r > 0.5 else "#f39c12" if r > 0.3 else "#e74c3c" for r in r2_scores]
    axes[0, 0].barh(categories, r2_scores, color=colors)
    axes[0, 0].set_title("Model Accuracy by Business Type (R2)", fontsize=13, fontweight="bold")
    axes[0, 0].set_xlabel("R2 Score")
    axes[0, 0].set_xlim(0, 1)
    for i, v in enumerate(r2_scores):
        axes[0, 0].text(v + 0.02, i, f"{v:.3f}", va="center", fontweight="bold")

    # Plot 2: Actual vs Predicted for best category
    best_cat = max(all_results, key=lambda x: all_results[x]["R2"])
    y_test = all_results[best_cat]["y_test"]
    y_pred = all_results[best_cat]["y_pred"]
    axes[0, 1].scatter(y_test, y_pred, alpha=0.5, s=20, color="#2ecc71")
    max_val = max(y_test.max(), max(y_pred))
    axes[0, 1].plot([0, max_val], [0, max_val], "r--", linewidth=2)
    axes[0, 1].set_title(f"Actual vs Predicted: {best_cat}", fontsize=13, fontweight="bold")
    axes[0, 1].set_xlabel("Actual Visitors")
    axes[0, 1].set_ylabel("Predicted Visitors")

    # Plot 3: Feature importance (average across all categories)
    all_features = all_results[categories[0]]["features"]
    avg_imp = np.zeros(len(all_features))
    for cat in categories:
        imp = all_results[cat]["importances"]
        if len(imp) == len(avg_imp):
            avg_imp += imp
    avg_imp /= len(categories)
    feat_imp = sorted(zip(all_features, avg_imp), key=lambda x: x[1], reverse=True)
    feat_names = [f[0] for f in feat_imp[:10]]
    feat_vals = [f[1] for f in feat_imp[:10]]
    axes[1, 0].barh(feat_names, feat_vals, color="#3498db")
    axes[1, 0].set_title("Top Features (Avg Across Categories)", fontsize=13, fontweight="bold")
    axes[1, 0].invert_yaxis()

    # Plot 4: RMSE by category
    rmse_scores = [all_results[c]["RMSE"] for c in categories]
    axes[1, 1].barh(categories, rmse_scores, color="#e74c3c")
    axes[1, 1].set_title("Prediction Error by Business (RMSE)", fontsize=13, fontweight="bold")
    axes[1, 1].set_xlabel("RMSE (visitors)")

    plt.tight_layout()
    plt.savefig("data/processed/prediction_model.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Saved: data/processed/prediction_model.png")

def predict_scenarios(all_models, all_results):
    print("\n" + "=" * 50)
    print("  SCENARIO PREDICTIONS")
    print("  'Given tomorrow's weather, how many visitors?'")
    print("=" * 50)

    scenarios = [
        {"name": "Hot Sunny Saturday in July",
         "weather": {"temp_avg_f": 95, "precip_inches": 0, "weather_severity": 1,
                     "is_weekend": 1, "month": 7, "day_of_week": 5}},
        {"name": "Rainy Tuesday in April",
         "weather": {"temp_avg_f": 65, "precip_inches": 1.5, "weather_severity": 3,
                     "is_weekend": 0, "month": 4, "day_of_week": 1}},
        {"name": "Snowy Wednesday in January",
         "weather": {"temp_avg_f": 30, "precip_inches": 0.5, "weather_severity": 4,
                     "is_weekend": 0, "month": 1, "day_of_week": 2}},
    ]

    for s in scenarios:
        print(f"\n  {s['name']}:")
        print(f"  " + "-" * 45)
        for cat in sorted(all_models.keys()):
            features = all_results[cat]["features"]
            row = pd.DataFrame(0, index=[0], columns=features)
            for key, val in s["weather"].items():
                if key in row.columns:
                    row[key] = val
            # Set weather category dummies
            if s["weather"]["precip_inches"] > 0.5:
                if "weather_category_rainy" in row.columns:
                    row["weather_category_rainy"] = 1
            if s["weather"]["temp_avg_f"] < 32 and s["weather"]["precip_inches"] > 0:
                if "weather_category_snowy" in row.columns:
                    row["weather_category_snowy"] = 1

            pred = all_models[cat].predict(row)[0]
            print(f"    {cat:20s} -> {pred:.0f} visitors")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  PRICE OF WEATHER: Prediction Model v2")
    print("  One model per business category")
    print("=" * 50)

    df = load_data()
    print(f"\n  Loaded {len(df)} records")

    all_results, all_models = train_per_category(df)

    # Summary
    avg_r2 = np.mean([all_results[c]["R2"] for c in all_results])
    print(f"\n  Average R2 across all categories: {avg_r2:.3f} ({avg_r2*100:.1f}%)")

    plot_results(all_results)
    predict_scenarios(all_models, all_results)

    print("\n" + "=" * 50)
    print("  PREDICTION MODEL COMPLETE!")
    print("=" * 50)