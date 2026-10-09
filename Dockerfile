# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps: build tools for any C extensions,
# ca-certificates for OpenSSL to have a base trust store,
# libmariadb fallback for mysqlclient-style drivers.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        gcc \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

# Python deps (cached layer)
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# App code
COPY connection_db.py .
COPY api.py .

# Ensure /tmp is writable (default on slim images) and expose port
EXPOSE 8000

CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]
