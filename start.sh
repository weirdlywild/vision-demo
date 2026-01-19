#!/bin/bash
# Railway startup script that uses the PORT environment variable

# Use Railway's PORT if set, otherwise default to 8000
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT"
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
