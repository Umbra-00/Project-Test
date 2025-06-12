# Use a lightweight Python base image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Set environment variables for the database connection
# IMPORTANT: For production, use Docker Secrets or Kubernetes Secrets for secure management.
ENV DB_HOST=localhost
ENV DB_PORT=5432
ENV DB_NAME=learning_platform_db
ENV DB_USER=learning_user
ENV DB_PASSWORD=1469

# Expose any ports your application might listen on (e.g., if you add a FastAPI app later)
EXPOSE 8000

# Command to run your application (e.g., a simple script, or later your FastAPI app)
CMD ["uvicorn", "src.api.v1.main:app", "--host", "0.0.0.0", "--port", "8000"] 