# Stage 1: build the React frontend (only dist/ is kept)
FROM node:22-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: the image that actually runs
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8001 \
    DB_PATH=/app/data/xclipboard.db

# Run as a non-root user whose UID matches the host user that owns the data folder
ARG UID=1000
RUN useradd --uid ${UID} --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY back/ ./back/
COPY db/CreateTables.py ./db/
COPY --from=frontend /app/frontend/dist ./frontend/dist
RUN mkdir -p data logs && chown app:app data logs

USER app
EXPOSE 8001
CMD ["python", "back/ClipBackend.py"]
