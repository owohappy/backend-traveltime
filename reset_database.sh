#!/bin/bash
# Database Reset Script for TravelTime Backend
# This script safely resets the development database

echo "🔄 TravelTime Database Reset Script"
echo "=================================="

# Check if server is running
if pgrep -f "uvicorn.*main:app" > /dev/null; then
    echo "📡 Stopping running server..."
    pkill -f uvicorn
    sleep 2
else
    echo "📡 No server running"
fi

# Backup current database if it exists
if [ -f "db/traveltime_debug.db" ]; then
    echo "💾 Creating backup of current database..."
    cp db/traveltime_debug.db "db/traveltime_debug_backup_$(date +%Y%m%d_%H%M%S).db"
    
    echo "🗑️ Removing old database..."
    rm db/traveltime_debug.db
else
    echo "📂 No existing database found"
fi

echo "✅ Database reset complete!"
echo ""
echo "🚀 To restart the server with fresh schema:"
echo "   uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
echo ""
echo "📋 After restart, you can create a new test user:"
echo '   curl -X POST -H "Content-Type: application/json" \'
echo '     -d '"'"'{"email": "test@example.com", "password": "password123", "name": "Test User", "username": "testuser", "phonenumber": "1234567890", "address": "123 Test St"}'"'"' \'
echo '     http://localhost:8001/register'
