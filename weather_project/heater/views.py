import pandas as pd
import requests
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render

# Dati comuni
GGR_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/osservativi/aggregationComuniErg5_DAILY_DEGREEDAYS_HEATING.csv"
GGC_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/osservativi/aggregationComuniErg5_DAILY_DEGREEDAYS_COOLING.csv"

# Comune scelto: Modena
COMUNE_CODE = "155_AVG_D"

# Fascia climatica E: 15 ottobre - 15 aprile
HEATING_START = (10, 15)  # (mese, giorno)
HEATING_END = (4, 15)

# Raffrescamento: 1 maggio - 30 settembre
COOLING_START = (5, 1)
COOLING_END = (9, 30)


def fetch_gdd_data(url):
    """Fetch and load gradi giorno data."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return None, f"Errore nel caricamento dati: {e}"

    from io import StringIO
    df = pd.read_csv(StringIO(response.text), parse_dates=["Date"])

    if "Date" not in df.columns or COMUNE_CODE not in df.columns:
        return None, "Colonne mancanti nei dati."

    return df, None


def compute_heating_seasons(df_hdd):
    """Compute cumulative Heating Degree Days per season."""
    df_hdd = df_hdd[["Date", COMUNE_CODE]].dropna()
    df_hdd["Year"] = df_hdd["Date"].dt.year
    df_hdd["Month"] = df_hdd["Date"].dt.month
    df_hdd["Day"] = df_hdd["Date"].dt.day

    records = []
    for year in range(2001, datetime.now().year + 1):
        # Heating season spans from 15 October (year-1) to 15 April (year)
        start_date = pd.Timestamp(year=year-1, month=HEATING_START[0], day=HEATING_START[1])
        end_date = pd.Timestamp(year=year, month=HEATING_END[0], day=HEATING_END[1])

        season_df = df_hdd[(df_hdd["Date"] >= start_date) & (df_hdd["Date"] <= end_date)]

        # Handle leap years if necessary
        is_leap = (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))
        cumulative = season_df[COMUNE_CODE].sum()

        records.append({
            "Season": f"{year-1}/{year}",
            "Heating_Degree_Days": cumulative*0.01,
            "Leap_Year": "Yes" if is_leap else "No"
        })

    return pd.DataFrame(records)


def compute_cooling_seasons(df_cdd):
    """Compute cumulative Cooling Degree Days per year."""
    df_cdd = df_cdd[["Date", COMUNE_CODE]].dropna()
    df_cdd["Year"] = df_cdd["Date"].dt.year
    df_cdd["Month"] = df_cdd["Date"].dt.month
    df_cdd["Day"] = df_cdd["Date"].dt.day

    records = []
    for year in range(2001, datetime.now().year + 1):
        start_date = pd.Timestamp(year=year, month=COOLING_START[0], day=COOLING_START[1])
        end_date = pd.Timestamp(year=year, month=COOLING_END[0], day=COOLING_END[1])

        season_df = df_cdd[(df_cdd["Date"] >= start_date) & (df_cdd["Date"] <= end_date)]

        cumulative = season_df[COMUNE_CODE].sum()

        records.append({
            "Year": year,
            "Cooling_Degree_Days": cumulative*0.01
        })

    return pd.DataFrame(records)


def heating_and_cooling_table(request):
    """Render heating and cooling degree days tables."""
    df_hdd, error_hdd = fetch_gdd_data(GGR_URL)
    df_cdd, error_cdd = fetch_gdd_data(GGC_URL)

    if error_hdd or error_cdd:
        return JsonResponse({"error": error_hdd or error_cdd}, status=500)

    heating_table = compute_heating_seasons(df_hdd)
    cooling_table = compute_cooling_seasons(df_cdd)

    # Return data to be shown in a page
    context = {
        "heating_table": heating_table.to_dict(orient="records"),
        "cooling_table": cooling_table.to_dict(orient="records"),
        "current_year": datetime.now().year
    }
    return render(request, "heater/heater.html", context)


def get_heating_cooling_data(request):
    """Optional API to serve data via JSON."""
    df_hdd, error_hdd = fetch_gdd_data(GGR_URL)
    df_cdd, error_cdd = fetch_gdd_data(GGC_URL)

    if error_hdd or error_cdd:
        return JsonResponse({"error": error_hdd or error_cdd}, status=500)

    heating_table = compute_heating_seasons(df_hdd)
    cooling_table = compute_cooling_seasons(df_cdd)

    data = {
        "heating": heating_table.to_dict(orient="records"),
        "cooling": cooling_table.to_dict(orient="records"),
    }

    return JsonResponse(data, safe=False)
