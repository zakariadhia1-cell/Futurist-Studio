FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt
# Chromium for the Browser Automation feature (app/live/browser_manager.py).
RUN playwright install --with-deps chromium

COPY . .
RUN chmod +x docker-entrypoint.sh
RUN mkdir -p workspaces

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
