import pandas as pd
import requests
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# URL sorgenti
PRECIPITATION_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/osservativi/aggregationComuniErg5_DAILY_PREC.csv"
COMUNI_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/comuni.csv"

def fetch_precipitation_data():
    try:
        response = requests.get(PRECIPITATION_URL, timeout=10)
        response.raise_for_status()
        from io import StringIO
        df = pd.read_csv(StringIO(response.text), parse_dates=["Date"])
        return df, None
    except requests.RequestException as e:
        return None, f"Errore nel caricamento dei dati: {e}"

def load_comuni_mapping():
    try:
        df = pd.read_csv(COMUNI_URL, sep=",")
        df.columns = [c.strip() for c in df.columns]
        return {f"{int(row['Id'])}_AVG_D": row['Nome'] for _, row in df.iterrows()}
    except Exception as e:
        print(f"Errore caricamento comuni.csv: {e}")
        return {}

def compute_precipitation_series(df, code):
    df = df[["Date", code]].dropna()
    df = df.rename(columns={code: "precip"})
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Day"] = df["Date"].dt.day
    df["DayOfYear"] = df["Date"].dt.dayofyear
    df.loc[(df["Month"] == 2) & (df["Day"] == 29), "DayOfYear"] = 59  # Normalizzazione anni bisestili

    # Dati anno corrente
    current_year = datetime.now().year
    df_current = df[df["Year"] == current_year].copy()
    df_current["Cumulative"] = df_current["precip"].cumsum()

    # Climatologia 2001–2020
    df_hist = df[(df["Year"] >= 2001) & (df["Year"] <= 2020)].copy()
    df_hist = df_hist[~((df_hist["Month"] == 2) & (df_hist["Day"] == 29))]
    df_hist = df_hist.groupby(["DayOfYear", "Year"])["precip"].mean().reset_index()
    df_hist = df_hist.pivot(index="DayOfYear", columns="Year", values="precip").fillna(0)
    df_hist_cum = df_hist.cumsum()

    p25 = df_hist_cum.quantile(0.25, axis=1)
    p75 = df_hist_cum.quantile(0.75, axis=1)
    climate_max = df_hist_cum.max(axis=1)

    df_current["p25"] = df_current["DayOfYear"].map(p25)
    df_current["p75"] = df_current["DayOfYear"].map(p75)
    df_current["climate_max"] = df_current["DayOfYear"].map(climate_max)

    return df_current[["Date", "Cumulative", "p25", "p75", "climate_max"]]

@csrf_exempt
def precipitation_chart(request):
    selected_code = request.GET.get("comune", "155_AVG_D")

    df, error = fetch_precipitation_data()
    if error:
        return JsonResponse({"error": error}, status=500)

    try:
        df_result = compute_precipitation_series(df, selected_code)
    except Exception as e:
        return JsonResponse({"error": f"Elaborazione fallita: {e}"}, status=500)

    result = {
        "date": df_result["Date"].dt.strftime("%Y-%m-%d").tolist(),
        "cumulative": df_result["Cumulative"].tolist(),
        "p25": df_result["p25"].tolist(),
        "p75": df_result["p75"].tolist(),
        "climate_max": df_result["climate_max"].tolist(),
    }
    return JsonResponse(result)

def precipitation_page(request):
    comuni_mapping = load_comuni_mapping()
    comuni = [{"code": code, "name": name} for code, name in comuni_mapping.items()]
    return render(request, "precipitation/precipitation.html", {
        "comuni": comuni,
        "selected_comune": "155_AVG_D",
    })
