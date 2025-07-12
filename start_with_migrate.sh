#!/usr/bin/env bash
set -e

echo "Starting Umbra Educational Data Platform..."

# Function to check if database is ready
check_database() {
    python3 -c "
import os
import sys
import time
from sqlalchemy import create_engine, text

database_url = os.getenv('DATABASE_URL')
if not database_url:
    print('DATABASE_URL not set')
    sys.exit(1)

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Check if courses table exists
            result = conn.execute(text('SELECT to_regclass(\"public.courses\")'))
            table_exists = result.scalar() is not None
            if table_exists:
                print('Database and tables are ready!')
                sys.exit(0)
            else:
                print(f'Tables not ready yet, attempt {retry_count + 1}/{max_retries}')
    except Exception as e:
        print(f'Database not ready: {e}, attempt {retry_count + 1}/{max_retries}')
    
    retry_count += 1
    time.sleep(2)

print('Database check timed out')
sys.exit(1)
"
}

echo "Checking database connection and tables..."
check_database

echo "Database is ready, starting application..."

# Start the backend server
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.v1.main:app --bind 0.0.0.0:$PORT 
