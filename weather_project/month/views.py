import pandas as pd
import plotly.graph_objs as go
import json
import requests
from django.http import JsonResponse
from django.shortcuts import render

TMIN_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/osservativi/aggregationComuniErg5_DAILY_TMIN.csv"
TMAX_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/osservativi/aggregationComuniErg5_DAILY_TMAX.csv"

COMMON_NAME = "155_AVG_D"  # Modena column

def fetch_weather_data():
    """Fetch temperature data from external sources."""
    tmin_df = pd.read_csv(TMIN_URL, parse_dates=["Date"])
    tmax_df = pd.read_csv(TMAX_URL, parse_dates=["Date"])
    
    # Keep only the last 30 days
    last_30_days = pd.Timestamp.today() - pd.DateOffset(days=30)
    tmin_df = tmin_df[tmin_df["Date"] >= last_30_days]
    tmax_df = tmax_df[tmax_df["Date"] >= last_30_days]

    # Extract Modena data
    tmin_df = tmin_df[["Date", COMMON_NAME]].rename(columns={COMMON_NAME: "TMIN"})
    tmax_df = tmax_df[["Date", COMMON_NAME]].rename(columns={COMMON_NAME: "TMAX"})

    # Merge dataframes
    df = pd.merge(tmin_df, tmax_df, on="Date")
    
    # Calculate percentiles (25th and 75th)
    df["P25"] = df[["TMIN", "TMAX"]].quantile(0.25, axis=1)
    df["P75"] = df[["TMIN", "TMAX"]].quantile(0.75, axis=1)

    return df

def process_month_data(request):
    """Return JSON data for the chart."""
    df = fetch_weather_data()
    
    data = {
        "date": df["Date"].dt.strftime('%Y-%m-%d').tolist(),
        "tmin": df["TMIN"].tolist(),
        "tmax": df["TMAX"].tolist(),
        "p25": df["P25"].tolist(),
        "p75": df["P75"].tolist(),
    }
    
    return JsonResponse(data)

def month_chart(request):
    """Render the month.html template."""
    return render(request, "month/month.html")
