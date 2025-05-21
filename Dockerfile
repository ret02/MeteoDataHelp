# Usa una base Python
FROM python:3.10-slim

# Imposta directory di lavoro
WORKDIR /app

# Copia e installa dipendenze
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia tutto il progetto Django
COPY weatherMap/ .

# Espone la porta per il runserver
EXPOSE 8000

# Comando per avviare Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
