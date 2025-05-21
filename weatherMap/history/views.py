import pandas as pd
import numpy as np
import requests
import io
import plotly.graph_objects as go
from django.shortcuts import render

# URL dei dati
CSV_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/osservativi/aggregationComuniErg5_DAILY_TAVG.csv"
COMUNI_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/comuni.csv"

# Carica i comuni come dizionario { "155_AVG_D": "Modena", ... }
def load_comuni_mapping():
    df = pd.read_csv(COMUNI_URL)
    return {f"{int(row['Id'])}_AVG_D": row["Nome"] for _, row in df.iterrows()}

# Carica e prepara i dati per un dato comune (es. "155_AVG_D")
def history_data(comune_code):
    response = requests.get(CSV_URL)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text), sep=",")

    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    if comune_code not in df.columns:
        raise ValueError(f"Comune '{comune_code}' non trovato nei dati CSV")

    df = df[["Date", comune_code]].rename(columns={comune_code: "TAVG"})
    df['Year'] = df['Date'].dt.year
    df['DayOfYear'] = df['Date'].dt.dayofyear
    df['Month'] = df['Date'].dt.month

    # Statistiche storiche 2001–2020
    historical_data = df[df['Year'].between(2001, 2020)]
    daily_stats = historical_data.groupby('DayOfYear')['TAVG'].agg([
        'min', 'max',
        lambda x: np.percentile(x, 25),
        lambda x: np.percentile(x, 75)
    ])
    daily_stats.columns = ['Min', 'Max', 'Percentile_25', 'Percentile_75']

    # Dati anno corrente
    current_year = pd.to_datetime('today').year
    current_year_data = df[df['Year'] == current_year].groupby('DayOfYear')['TAVG'].mean()

    # Medie mensili storiche
    monthly_means = historical_data.groupby(['Year', 'Month'])['TAVG'].mean().reset_index()

    return daily_stats, current_year_data, daily_stats['Max'].max(), daily_stats['Min'].min(), monthly_means

# View principale
def history_view(request):
    comuni = load_comuni_mapping()
    comune_code = request.GET.get("comune", "155_AVG_D")  # Default: Modena

    try:
        daily_stats, current_year_data, historical_max, historical_min, monthly_means = history_data(comune_code)
    except ValueError as e:
        return render(request, "history/history.html", {
            'error': str(e),
            'comuni': comuni,
            'selected_comune': comune_code,
        })

    monthly_data = monthly_means.head(12).to_dict("records")

    # Costruzione grafico Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=current_year_data.index, y=current_year_data.values,
        mode='lines', name=f'Anno Corrente ({pd.to_datetime("today").year})', line=dict(color='blue')
    ))
    fig.add_trace(go.Scatter(
        x=daily_stats.index, y=daily_stats['Min'],
        mode='lines', name='Min Temp', line=dict(color='gray')
    ))
    fig.add_trace(go.Scatter(
        x=daily_stats.index, y=daily_stats['Max'],
        mode='lines', name='Max Temp', line=dict(color='gray')
    ))
    fig.add_trace(go.Scatter(
        x=daily_stats.index, y=daily_stats['Percentile_25'],
        mode='lines', name='25° percentile', line=dict(color='red', dash='dot')
    ))
    fig.add_trace(go.Scatter(
        x=daily_stats.index, y=daily_stats['Percentile_75'],
        mode='lines', name='75° percentile', line=dict(color='green', dash='dot')
    ))

    fig.update_layout(
        title="Confronto Storico Temperature Medie",
        xaxis_title="Giorno dell'anno",
        yaxis_title="Temperatura (°C)",
        template="plotly_dark",
        hovermode="x unified"
    )

    graph_html = fig.to_html(full_html=False)
    nome_comune = comuni.get(comune_code, "Comune sconosciuto")

    return render(request, "history/history.html", {
        'graph_html': graph_html,
        'historical_max': round(historical_max, 1),
        'historical_min': round(historical_min, 1),
        'monthly_data': monthly_data,
        'selected_comune': comune_code,
        'nome_comune': nome_comune,
        'comuni': comuni,
    })
