import pandas as pd
import numpy as np
import requests
import io
import plotly.graph_objects as go
from django.shortcuts import render


CSV_URL = "https://dati-simc.arpae.it/opendata/osservatorio-clima/meteo-comunale/osservativi/aggregationComuniErg5_DAILY_TAVG.csv"

def history_data():
    # Fetch the CSV file from the URL
    response = requests.get(CSV_URL)
    response.raise_for_status()  # Raise an error if the request fails

    # Load the CSV file into a DataFrame
    df = pd.read_csv(io.StringIO(response.text), sep=",")
    
    # Convert the 'Date' column to datetime format
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    # Melt the DataFrame to transform the daily columns into a single column of temperatures
    melted_df = df.melt(id_vars=['Date'], var_name='Day', value_name='TAVG')

    # Extract year and day of year (DOY)
    melted_df['Year'] = melted_df['Date'].dt.year
    melted_df['DayOfYear'] = melted_df['Date'].dt.dayofyear

    # Compute daily percentiles (25th and 75th) and min/max for each day across the years 2001 to 2020
    historical_data = melted_df[melted_df['Year'].between(2001, 2020)]
    
    daily_stats = historical_data.groupby('DayOfYear')['TAVG'].agg([
        'min', 'max', lambda x: np.percentile(x, 25), lambda x: np.percentile(x, 75)
    ])
    
    daily_stats.columns = ['Min', 'Max', 'Percentile_25', 'Percentile_75']

    # Get the current year's data
    current_year = pd.to_datetime('today').year
    current_year_data = melted_df[melted_df['Year'] == current_year].groupby('DayOfYear')['TAVG'].mean()
    historical_max = daily_stats['Max'].max()
    historical_min = daily_stats['Min'].min()

    # Calcola le medie mensili (esempio)
    melted_df['Month'] = melted_df['Date'].dt.month
    monthly_means = melted_df[melted_df['Year'].between(2001, 2020)].groupby(['Year', 'Month'])['TAVG'].mean().reset_index()

    return daily_stats, current_year_data, historical_max, historical_min, monthly_means

def history_view(request):
    # Fetch all data
    daily_stats, current_year_data, historical_max, historical_min, monthly_means = history_data()

    # Convert monthly means to a format suitable for the template
    monthly_data = monthly_means.head(12).to_dict('records')  # Prendi solo i primi 12 per esempio
    # Create a Plotly figure for the chart
    fig = go.Figure()

    # Add the current year's temperature line
    fig.add_trace(go.Scatter(x=current_year_data.index, y=current_year_data.values,
                             mode='lines', name=f'Current Year ({pd.to_datetime("today").year})', line=dict(color='blue')))

    # Add the historical min, max, and percentiles
    fig.add_trace(go.Scatter(x=daily_stats.index, y=daily_stats['Min'],
                             mode='lines', fill='tonexty', name='Min Temp', line=dict(color='gray')))
    fig.add_trace(go.Scatter(x=daily_stats.index, y=daily_stats['Max'],
                             mode='lines', fill='tonexty', name='Max Temp', line=dict(color='gray')))
    fig.add_trace(go.Scatter(x=daily_stats.index, y=daily_stats['Percentile_25'],
                             mode='lines', name='25th Percentile', line=dict(color='red', dash='dot')))
    fig.add_trace(go.Scatter(x=daily_stats.index, y=daily_stats['Percentile_75'],
                             mode='lines', name='75th Percentile', line=dict(color='green', dash='dot')))

    # Layout settings
    fig.update_layout(
        title="Daily Temperature Comparison: Current Year vs Historical Data",
        xaxis_title="Day of Year",
        yaxis_title="Temperature (°C)",
        template="plotly_dark",
        hovermode="x unified"
    )

    # Convert the Plotly graph to HTML to embed in Django
    graph_html = fig.to_html(full_html=False)

    return render(request, "history/history.html", {
        'graph_html': graph_html,
        'historical_max': round(historical_max, 1),
        'historical_min': round(historical_min, 1),
        'monthly_data': monthly_data
    })
