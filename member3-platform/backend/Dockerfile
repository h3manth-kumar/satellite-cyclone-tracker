FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for geospatial tools if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create directory for satellite image assets
RUN mkdir -p /app/data/satellite/raw /app/data/satellite/explainability

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
