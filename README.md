\# The Price of Weather: Dallas Business Impact Analysis



\## How does weather affect local business foot traffic in Dallas, TX?



This project analyzes 12 months of weather data against 8 business categories to quantify weather's financial impact on local businesses. Using statistical testing and machine learning, it reveals which businesses thrive or suffer under different weather conditions.



\## Key Findings



\- \*\*Parks lose 84% of visitors\*\* on rainy days vs clear days

\- \*\*Ice cream shops drop 52%\*\* during rain

\- \*\*Movie theaters gain 35%\*\* on rainy days (people go indoors!)

\- \*\*Shopping malls are most resilient\*\* with only 15% drop

\- Customer sentiment drops from \*\*0.77 (clear) to 0.58 (rainy)\*\*

\- All findings are \*\*statistically significant\*\* (p < 0.05)



\## Tech Stack



| Layer | Tools |

|-------|-------|

| Data Collection | Python, OpenWeatherMap API, Google Places API, Yelp API |

| Cloud Storage | Google BigQuery |

| Pipeline | Prefect (automated ETL) |

| Analysis | pandas, scipy, scikit-learn |

| Visualization | Power BI (4-page dashboard), Streamlit (interactive web app) |

| Charts | matplotlib, seaborn, plotly |



\## Project Structure



```

price-of-weather/

├── scripts/

│   ├── fetch\_weather.py          # Current weather API

│   ├── fetch\_historical\_weather.py # 12-month weather data

│   ├── fetch\_businesses.py       # Google Places API

│   ├── fetch\_yelp\_reviews.py     # Yelp business data

│   ├── upload\_to\_bigquery.py     # BigQuery upload

│   ├── pipeline.py               # Prefect ETL pipeline

│   ├── clean\_and\_merge.py        # Data cleaning

│   ├── simulate\_traffic.py       # Foot traffic model

│   ├── analyze\_v2.py             # Statistical analysis

│   ├── predict\_traffic.py        # ML prediction model

│   ├── export\_for\_powerbi.py     # Power BI data prep

│   └── app.py                    # Streamlit web app

├── config/                       # API keys (gitignored)

├── data/

│   ├── raw/                      # Raw API data

│   └── processed/                # Cleaned analysis data

├── requirements.txt

└── README.md

```



\## Dashboard Preview



\### Power BI Dashboard

\*4-page interactive dashboard with weather impact analysis, business comparisons, and sentiment scoring.\*



\### Streamlit Web App

\*Interactive web application with filters, heatmaps, and a weather prediction simulator.\*



\## How to Run



1\. Clone this repo

2\. Install dependencies: `pip install -r requirements.txt`

3\. Add your API keys in `config/secrets.py`

4\. Add BigQuery service account key as `config/bigquery\_key.json`

5\. Run the pipeline: `python scripts/pipeline.py`

6\. Launch the app: `streamlit run scripts/app.py`



\## Statistical Methods



\- \*\*T-tests\*\*: Comparing visitor counts between weather conditions

\- \*\*Pearson correlation\*\*: Temperature and precipitation vs foot traffic

\- \*\*Random Forest regression\*\*: Predicting visitors given weather forecast

\- \*\*Sentiment analysis\*\*: Customer mood scoring by weather condition



\## Data Sources



\- OpenWeatherMap API (current weather)

\- Visual Crossing API (12-month historical weather)

\- Google Places API (business locations and ratings)

\- Yelp Fusion API (business reviews and ratings)



\## Author



\*\*Shanmuga Kothapalli\*\*

\*Mid-Level Data Analyst | Dallas, TX\*

