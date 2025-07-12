FROM python:3.11.4-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for psycopg2 (PostgreSQL client)
# and other potential build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python dependencies first
# This allows Docker to cache the layer if requirements.txt doesn't change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure scripts are executable for deployment
RUN chmod +x scripts/*.sh || true

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port that the application will listen on.
# Render automatically injects the $PORT environment variable.
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Command to run the FastAPI application using Uvicorn (used for local testing and potentially for Render direct deploy)
# For Render, the 'startCommand' in render.yaml will override this CMD.
CMD ["uvicorn", "src.api.v1.main:app", "--host", "0.0.0.0", "--port", "8000"]
