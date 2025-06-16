# Use a specific Python base image for consistency with backend
FROM python:3.11.4-slim

# Set environment variables for Python
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy requirements file and install Python dependencies
# Note: We assume requirements.txt is at the project root for consistency.
# If your frontend has a separate requirements.txt in frontend/, adjust this path.
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the frontend application code
COPY frontend/ /app/frontend

# Expose the default Streamlit port (Render will map this)
EXPOSE 8501

# Command to run the Streamlit application
# Render's 'startCommand' in render.yaml will override this CMD for deployment.
CMD ["streamlit", "run", "frontend/app.py", "--server.port", "8501", "--server.enableCORS", "false"]
