FROM node:24-slim AS web
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=web /app/backend/frontend_dist ./frontend_dist
RUN useradd --create-home app
USER app
EXPOSE 8000
# Hosts such as Render and Cloud Run pass the port to listen on in $PORT.
CMD ["sh", "-c", "exec gunicorn config.wsgi --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 8 --timeout 120"]
