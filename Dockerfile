FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI
RUN apt-get update && \
    apt-get install -y docker.io git curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app /app/app

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
