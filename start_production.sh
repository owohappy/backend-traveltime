#!/bin/bash

echo "Starting TravelTime API in prod mode..."

export APP_DEBUG=false
export PYTHONPATH=/app
export PYTHONUNBUFFERED=1

mkdir -p db log misc/templates/pfp

exec uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --access-log \
    --log-level info
