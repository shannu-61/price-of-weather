import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(page_title="Price of Weather", page_icon="⛅", layout="wide")

# Load data
@st.cache_data
def load_data():
    traffic = pd.read_csv("data/processed/daily_traffic.csv")
    traffic["date"] = pd.to_datetime(traffic["date"])
    weather = pd.read_csv("data/processed/powerbi_weather.csv")
    weather["date"] = pd.to_datetime(weather["date"])
    return traffic, weather

traffic, weather = load_data()

# Title
st.title("⛅ The Price of Weather")
st.markdown("### How weather impacts Dallas businesses — a 12-month data study")
st.markdown("---")

# Sidebar filters
st.sidebar.header("Filters")
selected_categories = st.sidebar.multiselect(
    "Business Types",
    options=sorted(traffic["category"].unique()),
    default=sorted(traffic["category"].unique())
)
selected_weather = st.sidebar.multiselect(
    "Weather Conditions",
    options=sorted(traffic["weather_category"].unique()),
    default=sorted(traffic["weather_category"].unique())
)

# Filter data
filtered = traffic[
    (traffic["category"].isin(selected_categories)) &
    (traffic["weather_category"].isin(selected_weather))
]

# Row 1: KPI cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Records", f"{len(filtered):,}")
col2.metric("Avg Daily Visitors", f"{filtered['estimated_visitors'].mean():.0f}")
col3.metric("Business Types", f"{filtered['category'].nunique()}")
col4.metric("Avg Sentiment", f"{filtered['sentiment_score'].mean():.2f}")

st.markdown("---")

# Row 2: Two charts
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Average Visitors by Business Type")
    avg_by_cat = filtered.groupby("category")["estimated_visitors"].mean().sort_values(ascending=True).reset_index()
    fig1 = px.bar(avg_by_cat, x="estimated_visitors", y="category", orientation="h",
                  color="estimated_visitors", color_continuous_scale="blues")
    fig1.update_layout(showlegend=False, height=400, yaxis_title="", xaxis_title="Avg Visitors")
    st.plotly_chart(fig1, use_container_width=True)

with col_right:
    st.subheader("Weather Impact on Visitors")
    avg_by_weather = filtered.groupby(["weather_category", "category"])["estimated_visitors"].mean().reset_index()
    fig2 = px.bar(avg_by_weather, x="weather_category", y="estimated_visitors", color="category",
                  barmode="group")
    fig2.update_layout(height=400, xaxis_title="Weather", yaxis_title="Avg Visitors")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Row 3: Impact heatmap
st.subheader("Weather Impact Heatmap (% Change vs Clear Days)")
pivot = filtered.groupby(["weather_category", "category"])["estimated_visitors"].mean().unstack()
if "clear" in pivot.index:
    pct_change = pivot.copy()
    for col in pct_change.columns:
        clear_val = pct_change.loc["clear", col]
        pct_change[col] = ((pct_change[col] - clear_val) / clear_val) * 100
    fig3 = px.imshow(pct_change.round(1), text_auto=True, color_continuous_scale="RdYlGn",
                     color_continuous_midpoint=0, aspect="auto")
    fig3.update_layout(height=350)
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# Row 4: Sentiment
col_s1, col_s2 = st.columns(2)

with col_s1:
    st.subheader("Sentiment by Weather")
    sent_weather = filtered.groupby("weather_category")["sentiment_score"].mean().reset_index()
    fig4 = px.bar(sent_weather, x="weather_category", y="sentiment_score",
                  color="sentiment_score", color_continuous_scale="RdYlGn")
    fig4.update_layout(height=350, yaxis_title="Avg Sentiment", xaxis_title="Weather")
    st.plotly_chart(fig4, use_container_width=True)

with col_s2:
    st.subheader("Monthly Visitor Trend")
    filtered["month"] = filtered["date"].dt.month
    monthly = filtered.groupby("month")["estimated_visitors"].mean().reset_index()
    fig5 = px.line(monthly, x="month", y="estimated_visitors", markers=True)
    fig5.update_layout(height=350, xaxis_title="Month", yaxis_title="Avg Visitors")
    st.plotly_chart(fig5, use_container_width=True)

st.markdown("---")

# Row 5: Prediction simulator
st.subheader("🔮 Weather Prediction Simulator")
st.markdown("*What if tomorrow's weather is...*")

sim_col1, sim_col2, sim_col3 = st.columns(3)
with sim_col1:
    sim_temp = st.slider("Temperature (F)", 20, 110, 75)
with sim_col2:
    sim_rain = st.selectbox("Weather", ["clear", "cloudy", "rainy", "snowy"])
with sim_col3:
    sim_weekend = st.selectbox("Day Type", ["Weekday", "Weekend"])

# Simple prediction based on averages
is_wknd = 1 if sim_weekend == "Weekend" else 0
sim_data = traffic[(traffic["weather_category"] == sim_rain) & (traffic["is_weekend"] == is_wknd)]

if len(sim_data) > 0:
    st.markdown("**Predicted visitors:**")
    pred_cols = st.columns(4)
    for i, cat in enumerate(sorted(sim_data["category"].unique())):
        cat_avg = sim_data[sim_data["category"] == cat]["estimated_visitors"].mean()
        # Temperature adjustment
        temp_factor = 1 + (sim_temp - 70) * 0.003
        adjusted = cat_avg * temp_factor
        pred_cols[i % 4].metric(cat, f"{adjusted:.0f}")

st.markdown("---")
st.caption("Built by Shanmuga | Data: OpenWeatherMap, Google Places, Yelp | Dallas, TX 2024-2025")