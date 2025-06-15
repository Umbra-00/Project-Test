#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Deployment Script...${NC}"

# Check for required environment variables for deployment
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}Error: DATABASE_URL environment variable is not set. Exiting.${NC}"
    exit 1
fi
if [ -z "$SECRET_KEY" ]; then
    echo -e "${RED}Error: SECRET_KEY environment variable is not set. Exiting.${NC}"
    exit 1
fi
if [ -z "$INITIAL_ADMIN_PASSWORD" ]; then
    echo -e "${RED}Error: INITIAL_ADMIN_PASSWORD environment variable is not set. Exiting.${NC}"
    exit 1
fi

echo -e "${GREEN}Required environment variables are set.${NC}"

# 1. Prepare virtual environment
echo -e "${GREEN}1. Setting up virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# 2. Upgrade pip and install dependencies
echo -e "${GREEN}2. Installing project dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn uvicorn[standard] # Ensure production server is installed

# 3. Run database migrations
echo -e "${GREEN}3. Running database migrations...${NC}"
alembic upgrade head

# 4. Start the application using Gunicorn for production
echo -e "${GREEN}4. Starting the FastAPI application with Gunicorn...${NC}"
# Use Gunicorn to run the FastAPI app in a production-ready manner
# -w: number of worker processes
# -k: worker class (uvicorn.workers.UvicornWorker for FastAPI)
# --bind: host and port to bind to (use $PORT for Render)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.v1.main:app --bind 0.0.0.0:$PORT

# Deactivate virtual environment (this line might not be reached if gunicorn runs indefinitely)
# deactivate

echo -e "${GREEN}Deployment script completed. Application should be running.${NC}" 