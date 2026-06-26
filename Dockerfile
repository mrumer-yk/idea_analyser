# Backend image for the India Idea Validator API.
# Works on any container host (Render, Railway, Fly.io, etc.).
FROM python:3.12-slim

WORKDIR /app

# System deps: trafilatura/lxml pull in C extensions; slim base needs build bits
# only at install time. Keep the layer small.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y build-essential && apt-get autoremove -y

COPY backend ./backend

# Persist SQLite here; mount a volume at /data on the host for durable history.
ENV DATABASE_PATH=/data/app.db
EXPOSE 8000

# Honor the platform-provided $PORT (Render/Railway set it); default to 8000.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
