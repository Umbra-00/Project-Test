#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Color codes for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Local CI/CD Pipeline Test...${NC}"

# 1. Prepare virtual environment
echo -e "${GREEN}1. Setting up virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
echo -e "${GREEN}2. Installing project dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Ensure testing and code quality tools are installed
pip install pytest coverage ruff bandit black alembic

# 3. Run linters (Ruff and Black)
echo -e "${GREEN}3. Running Code Linters (Ruff and Black)...${NC}"
ruff check src/
ruff format --check src/
black --check src/

# 4. Run security scan (Bandit)
echo -e "${GREEN}4. Running Security Scan (Bandit)...${NC}"
bandit -r src/ -f custom # You might want to adjust the format or output

# 5. Run database migrations (for testing environment)
# Ensure your local postgres is running and accessible or mock it for tests
echo -e "${GREEN}5. Running database migrations for testing...${NC}"
# Set a dummy DATABASE_URL for local testing if not already set in .env
export DATABASE_URL="postgresql://test_user:test_password@localhost:5432/test_db"
# You might need to ensure your local PostgreSQL is running and has `test_db` with `test_user`
alembic upgrade head

# 6. Run unit tests with coverage
echo -e "${GREEN}6. Running Unit Tests with Coverage...${NC}"
coverage run -m pytest tests/
coverage report -m # Print summary to console
coverage xml # Generate XML report (e.g., for Codecov)

# 7. Deactivate virtual environment
echo -e "${GREEN}7. Deactivating virtual environment...${NC}"
deactivate

echo -e "${GREEN}Local CI/CD Pipeline Test Completed Successfully!${NC}" 