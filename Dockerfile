FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr (important for container logs)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/
COPY core/ ./core/
COPY data/ ./data/
COPY .streamlit/ ./.streamlit/

# Streamlit default port
EXPOSE 8501

# Health check for Render
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the app — server.address=0.0.0.0 is critical for containers
CMD ["streamlit", "run", "app/main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=true"]
