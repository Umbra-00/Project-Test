# Deployment Guide

This guide provides instructions for deploying the Umbra Data Science Platform locally using Docker Compose and to Render.com.

## Prerequisites
- Python 3.11+
- Docker (for local Docker deployment)
- Git
- Render Account (for cloud deployment)
- GitHub Account (for CI/CD)

## Local Development Setup

Follow these steps to set up and run the project on your local machine:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Create a Virtual Environment and Install Dependencies:**
    It's highly recommended to use a virtual environment.
    ```bash
    python -m venv venv
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    venv\Scripts\activate
    ```
    Then install the required Python packages:
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    Copy the example environment file and fill in your details.
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file and replace placeholder values (e.g., `your_secure_password`) with actual secure credentials. **Never commit your `.env` file to Git!**

4.  **Database Setup (Local PostgreSQL):**
    Ensure you have a local PostgreSQL server running or use Docker Compose as described below.
    Once your database is accessible (either local or via Docker), run database migrations:
    ```bash
    alembic upgrade head
    ```

5.  **Run with Docker Compose (Recommended for Local Dev):**
    This will spin up both the PostgreSQL database and the FastAPI backend, and Streamlit frontend.
    ```bash
    docker-compose up --build
    ```
    The backend will be available at `http://localhost:8000` and the frontend at `http://localhost:8501`.

## Render.com Cloud Deployment

This project is configured for deployment on Render.com using the `render.yaml` and `render.json` files.

### 1. Render Setup (One-Time)

*   **Create a Render Account:** If you don't have one, sign up at [Render.com](https://render.com/).
*   **Connect GitHub Repository:** Link your GitHub account to Render.
*   **Create a PostgreSQL Database:**
    *   In the Render dashboard, create a new PostgreSQL service.
    *   Name it `umbra-postgres` (this name is referenced in `render.yaml`).
    *   Note down the connection string and credentials, although Render will auto-inject these for services in the same blueprint.
*   **Configure GitHub Secrets:**
    Go to your GitHub repository **Settings > Secrets and variables > Actions** and add the following repository secrets:
    *   `RENDER_DEPLOY_HOOK`: Obtain this from your Render service settings after creating a web service.
    *   `DATABASE_URL`: (Optional, but good for explicit control) If you want to specify it directly, use the full connection string for your Render PostgreSQL database. Render's `fromDatabase` property handles this automatically.
    *   `SECRET_KEY`: Generate a strong, random key (e.g., `python3 -c 'import secrets; print(secrets.token_hex(32))'`).
    *   `INITIAL_ADMIN_PASSWORD`: Generate a strong, random password (e.g., `python3 -c 'import secrets; print(secrets.token_urlsafe(16))'`).

### 2. Deploying Services via Render.com

Render will use the `render.yaml` file to deploy your services.

*   **FastAPI Backend (`umbra-backend`):**
    *   **Type:** Web Service
    *   **Build Command:** `pip install -r requirements.txt`
    *   **Start Command:** `gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.v1.main:app --bind 0.0.0.0:$PORT`
    *   **Environment Variables:** Render will automatically inject `DATABASE_URL` from the `umbra-postgres` service. Ensure `SECRET_KEY`, `INITIAL_ADMIN_USERNAME`, and `INITIAL_ADMIN_PASSWORD` are set either as GitHub secrets or directly in Render's environment variable settings.

*   **Streamlit Frontend (`umbra-frontend`):**
    *   **Type:** Web Service
    *   **Build Command:** `pip install -r requirements.txt`
    *   **Start Command:** `streamlit run frontend/app.py --server.port $PORT --server.enableCORS false`
    *   **Environment Variables:** Render will automatically inject `BACKEND_URL` from the `umbra-backend` service.

## CI/CD Pipeline (GitHub Actions)

The project includes a GitHub Actions workflow (`.github/workflows/ci_cd.yml`) for continuous integration and deployment.

### 1. Local CI/CD Test

You can test the CI/CD pipeline locally before pushing to GitHub.
Make sure `scripts/local_ci_test.sh` is executable:
```bash
chmod +x scripts/local_ci_test.sh
```
Then run the script:
```bash
./scripts/local_ci_test.sh
```
This script will:
*   Set up a virtual environment.
*   Install dependencies.
*   Run code linters (Ruff, Black).
*   Perform a security scan (Bandit).
*   Run database migrations against a test database.
*   Execute unit tests with coverage.

### 2. GitHub Actions Workflow

The CI/CD workflow will automatically:
*   Run tests on every push and pull request to `main` and `develop` branches.
*   Perform security scans.
*   Enforce code quality checks.
*   **Deploy to Render:** If tests pass on the `main` branch, it will trigger a deployment to Render using the `RENDER_DEPLOY_HOOK` secret.

## Troubleshooting

*   **Database Connection Errors:**
    *   Ensure your `DATABASE_URL` is correct and accessible from your application (locally or on Render).
    *   Verify database credentials (username, password, host, port, database name).
    *   Check Render's PostgreSQL logs for connection issues.
    *   For local Docker, ensure the `db` service is healthy (`docker-compose ps`).
*   **Application Startup Failures:**
    *   Check application logs (locally or on Render).
    *   Verify `requirements.txt` includes all necessary dependencies.
    *   Ensure `startCommand` in `render.yaml` or `docker-compose.yml` is correct.
    *   Confirm environment variables are correctly set.
*   **Streamlit Frontend Not Connecting to Backend:**
    *   Verify `BACKEND_URL` environment variable on the frontend service.
    *   Ensure the backend service is running and accessible from the frontend.

Remember to replace placeholder values (e.g., `your-username`, `your-repo-name`, `your-render-postgres-host`) with your actual Render deployment details.