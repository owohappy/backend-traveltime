#!/bin/bash

# TravelTime API Production Startup Script
# This script starts the FastAPI backend server for production use

echo "=== TravelTime API Production Startup ==="
echo "$(date): Starting TravelTime API in production mode..."

# Environment configuration
export APP_DEBUG=false
export PYTHONPATH=/app
export PYTHONUNBUFFERED=1

# Create required directories
mkdir -p db log misc/templates/pfp

# Log startup information
echo "Environment:"
echo "  - Debug mode: $APP_DEBUG"
echo "  - Python path: $PYTHONPATH"
echo "  - Working directory: $(pwd)"
echo "  - Host: 0.0.0.0:8000"
echo "  - Workers: 4"

# Check if database exists
if [ -f "db/traveltime.db" ]; then
    echo "  - Database: Found ($(stat -f%z db/traveltime.db 2>/dev/null || stat -c%s db/traveltime.db) bytes)"
else
    echo "  - Database: Will be created automatically"
fi

# SSL information (for reference)
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    echo "  - SSL: Configured (handled by nginx)"
    echo "  - Certificate expires: $(openssl x509 -in ssl/cert.pem -noout -dates | grep notAfter | cut -d= -f2)"
else
    echo "  - SSL: Not configured (HTTP only)"
fi

echo ""
echo "Starting FastAPI server..."
echo "Access the API at:"
echo "  - Local: http://localhost:8000"
echo "  - Production: https://tt.owohappy.com (if SSL configured)"
echo ""

# Start the FastAPI server with production settings
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --access-log \
    --log-level info \
    --no-access-log-format \
    --date-header \
    --server-header
