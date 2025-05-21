import pandas as pd
import requests
from django.http import JsonResponse
from django.shortcuts import render

# URL dati
TMIN_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/osservativi/aggregationComuniErg5_DAILY_TMIN.csv"
TMAX_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/osservativi/aggregationComuniErg5_DAILY_TMAX.csv"
COMUNI_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/comuni.csv"

def load_comuni_mapping():
    try:
        df = pd.read_csv(COMUNI_URL, sep=",")
        df.columns = [c.strip() for c in df.columns]  # Pulizia nomi colonne
        return {f"{int(row['Id'])}_AVG_D": row['Nome'] for _, row in df.iterrows()}
    except Exception as e:
        print(f"Errore caricamento comuni.csv: {e}")
        return {}

def fetch_weather_data(comune_code="155_AVG_D"):
    """Fetch temperature data from external sources."""
    tmin_df = pd.read_csv(TMIN_URL, parse_dates=["Date"])
    tmax_df = pd.read_csv(TMAX_URL, parse_dates=["Date"])

    last_30_days = pd.Timestamp.today() - pd.DateOffset(days=30)
    tmin_df = tmin_df[tmin_df["Date"] >= last_30_days]
    tmax_df = tmax_df[tmax_df["Date"] >= last_30_days]

    # Estrai solo i dati del comune richiesto
    tmin_df = tmin_df[["Date", comune_code]].rename(columns={comune_code: "TMIN"})
    tmax_df = tmax_df[["Date", comune_code]].rename(columns={comune_code: "TMAX"})

    df = pd.merge(tmin_df, tmax_df, on="Date")

    df["P25"] = df[["TMIN", "TMAX"]].quantile(0.25, axis=1)
    df["P75"] = df[["TMIN", "TMAX"]].quantile(0.75, axis=1)

    return df

def process_month_data(request):
    """Return JSON data for the chart."""
    comune_code = request.GET.get("comune", "155_AVG_D")
    df = fetch_weather_data(comune_code)

    data = {
        "date": df["Date"].dt.strftime('%Y-%m-%d').tolist(),
        "tmin": df["TMIN"].tolist(),
        "tmax": df["TMAX"].tolist(),
        "p25": df["P25"].tolist(),
        "p75": df["P75"].tolist(),
    }

    return JsonResponse(data)

def month_chart(request):
    """Render the month.html template con lista comuni."""
    comuni_mapping = load_comuni_mapping()
    selected_code = request.GET.get("comune", "155_AVG_D")
    return render(request, "month/month.html", {
        "comuni": comuni_mapping,
        "selected_comune": selected_code,
    })
