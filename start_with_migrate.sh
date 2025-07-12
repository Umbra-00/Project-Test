#!/usr/bin/env bash
set -e

# Start the backend server
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.v1.main:app --bind 0.0.0.0:$PORT 