import pandas as pd
import requests
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render

# URL for precipitation data
PRECIPITATION_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/osservativi/aggregationComuniErg5_DAILY_PREC.csv"

# Modena's column
COMUNE_COLUMN = "155_AVG_D"

def process_precipitation_data():
    """Fetch and process precipitation data for Modena."""
    try:
        response = requests.get(PRECIPITATION_URL, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"Failed to retrieve data: {e}"}

    from io import StringIO
    df = pd.read_csv(StringIO(response.text), parse_dates=["Date"])

    if "Date" not in df.columns or COMUNE_COLUMN not in df.columns:
        return {"error": "Required columns missing"}

    df = df[["Date", COMUNE_COLUMN]].dropna()
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Day"] = df["Date"].dt.day
    df["DayOfYear"] = df["Date"].dt.dayofyear

    # Handle Feb 29: map to day 59 (Feb 28)
    df.loc[(df["Month"] == 2) & (df["Day"] == 29), "DayOfYear"] = 59

    # Current year
    current_year = datetime.now().year
    df_current = df[df["Year"] == current_year].copy()
    df_current["Cumulative"] = df_current[COMUNE_COLUMN].cumsum()

    # Historical years (2001–2020)
    df_hist = df[(df["Year"] >= 2001) & (df["Year"] <= 2020)].copy()

    # Drop Feb 29 if you want (optional safer)
    df_hist = df_hist[~((df_hist["Month"] == 2) & (df_hist["Day"] == 29))]

    # Group to remove duplicates
    df_hist = df_hist.groupby(["DayOfYear", "Year"])[COMUNE_COLUMN].mean().reset_index()

    # Pivot
    df_hist = df_hist.pivot(index="DayOfYear", columns="Year", values=COMUNE_COLUMN)

    # Fill missing with 0 (no rain)
    df_hist = df_hist.fillna(0)

    # Sort days
    df_hist = df_hist.sort_index()

    # Cumulative sum
    df_hist_cum = df_hist.cumsum()

    # Now compute percentiles per day
    p25 = df_hist_cum.quantile(0.25, axis=1)
    p75 = df_hist_cum.quantile(0.75, axis=1)
    climate_max = df_hist_cum.max(axis=1)

    # Map to current year days
    df_current["p25"] = df_current["DayOfYear"].map(p25)
    df_current["p75"] = df_current["DayOfYear"].map(p75)
    df_current["climate_max"] = df_current["DayOfYear"].map(climate_max)

    result = {
        "date": df_current["Date"].dt.strftime("%Y-%m-%d").tolist(),
        "cumulative": df_current["Cumulative"].tolist(),
        "p25": df_current["p25"].tolist(),
        "p75": df_current["p75"].tolist(),
        "climate_max": df_current["climate_max"].tolist(),
    }
    
    return result

def precipitation_chart(request):
    return render(request, "precipitations/precipitations.html")

def get_precipitation_data(request):
    data = process_precipitation_data()
    return JsonResponse(data, safe=False)
