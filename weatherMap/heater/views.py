import pandas as pd
import requests
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# URL dataset gradi giorno
GGR_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/osservativi/aggregationComuniErg5_DAILY_DEGREEDAYS_HEATING.csv"
GGC_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/osservativi/aggregationComuniErg5_DAILY_DEGREEDAYS_COOLING.csv"
COMUNI_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/comuni.csv"

# Periodi stagionali
HEATING_START = (10, 15)
HEATING_END = (4, 15)
COOLING_START = (5, 1)
COOLING_END = (9, 30)


def fetch_gdd_data(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        from io import StringIO
        df = pd.read_csv(StringIO(response.text), parse_dates=["Date"])
        return df, None
    except requests.RequestException as e:
        return None, f"Errore nel caricamento dati: {e}"


def load_comuni_mapping():
    try:
        df = pd.read_csv(COMUNI_URL, sep=",")  # Forziamo il separatore corretto
        df.columns = [c.strip() for c in df.columns]  # Pulizia nomi colonne

        # Ora ci aspettiamo colonne come 'Id', 'Istat', 'Nome', 'Provincia'
        return {f"{int(row['Id'])}_AVG_D": row['Nome'] for _, row in df.iterrows()}
    except Exception as e:
        print(f"Errore caricamento comuni.csv: {e}")
        return {}

def compute_heating_seasons(df_hdd, code):
    df_hdd = df_hdd[["Date", code]].dropna()
    df_hdd["Year"] = df_hdd["Date"].dt.year

    records = []
    for year in range(2001, datetime.now().year + 1):
        start = pd.Timestamp(year=year - 1, month=HEATING_START[0], day=HEATING_START[1])
        end = pd.Timestamp(year=year, month=HEATING_END[0], day=HEATING_END[1])
        season = df_hdd[(df_hdd["Date"] >= start) & (df_hdd["Date"] <= end)]
        cumulative = season[code].sum()
        records.append({
            "Season": f"{year - 1}/{year}",
            "Heating_Degree_Days": round(cumulative * 0.01, 2),
            "Leap_Year": "Yes" if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else "No"
        })
    return pd.DataFrame(records)


def compute_cooling_seasons(df_cdd, code):
    df_cdd = df_cdd[["Date", code]].dropna()
    df_cdd["Year"] = df_cdd["Date"].dt.year

    records = []
    for year in range(2001, datetime.now().year + 1):
        start = pd.Timestamp(year=year, month=COOLING_START[0], day=COOLING_START[1])
        end = pd.Timestamp(year=year, month=COOLING_END[0], day=COOLING_END[1])
        season = df_cdd[(df_cdd["Date"] >= start) & (df_cdd["Date"] <= end)]
        cumulative = season[code].sum()
        records.append({
            "Year": year,
            "Cooling_Degree_Days": round(cumulative * 0.01, 2)
        })
    return pd.DataFrame(records)


def heating_and_cooling_table(request):
    selected_code = request.GET.get("comune", "155_AVG_D")  # Default: Modena

    df_hdd, error_hdd = fetch_gdd_data(GGR_URL)
    df_cdd, error_cdd = fetch_gdd_data(GGC_URL)
    if error_hdd or error_cdd:
        return JsonResponse({"error": error_hdd or error_cdd}, status=500)

    comuni_mapping = load_comuni_mapping()
    comuni_codici = [col for col in df_hdd.columns if "_AVG_D" in col and col != "Date"]
    comuni = [{"code": code, "name": comuni_mapping.get(code, code)} for code in comuni_codici]

    heating_table = compute_heating_seasons(df_hdd, selected_code)
    cooling_table = compute_cooling_seasons(df_cdd, selected_code)

    context = {
        "comuni": comuni,
        "selected_comune": selected_code,
        "heating_table": heating_table.to_dict(orient="records"),
        "cooling_table": cooling_table.to_dict(orient="records"),
    }
    return render(request, "heater/heater.html", context)


@csrf_exempt
def get_heating_cooling_data(request):
    selected_code = request.GET.get("comune", "155_AVG_D")
    df_hdd, error_hdd = fetch_gdd_data(GGR_URL)
    df_cdd, error_cdd = fetch_gdd_data(GGC_URL)
    if error_hdd or error_cdd:
        return JsonResponse({"error": error_hdd or error_cdd}, status=500)

    heating_table = compute_heating_seasons(df_hdd, selected_code)
    cooling_table = compute_cooling_seasons(df_cdd, selected_code)

    return JsonResponse({
        "selected_comune": selected_code,
        "heating": heating_table.to_dict(orient="records"),
        "cooling": cooling_table.to_dict(orient="records"),
    })
