FROM python:3.11-slim

WORKDIR /app

# Copier le microservice + dossier commun
COPY ../common /app/common
COPY . /app

RUN pip install --no-cache-dir fastapi uvicorn kafka-python prometheus-fastapi-instrumentator prometheus-client

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
