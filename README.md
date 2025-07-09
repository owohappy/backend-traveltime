# TravelTime

An app that rewards users for taking public transportation instead of cars. The backend API tracks user travel routes and awards points for eco-friendly transportation choices.

## Features

- **Authentication**: User registration, login, logout, token refresh, and two-factor authentication
- **Account Management**: User profiles and points tracking
- **Travel Tracking**: GPS location monitoring to verify public transport usage
- **Route Management**: Route caching and spatial indexing  
- **Analytics**: Travel analytics with transport type detection
- **Performance**: Lazy loading and caching
- **Statistics**: Leaderboards and user stats
- **Admin Tools**: Route management and monitoring
- **Gambling**: Point gambling with Blackjack

## Analytics Features

### Route Analytics
- **Popular Routes**: Track most used routes
- **Operator Stats**: Market share and transport types
- **Pattern Learning**: Auto-detect bus/train/tram
- **User Insights**: Personal travel analytics
- **Dashboard**: System overview

### API Endpoints
- `/analytics/popular-routes` - Popular routes
- `/analytics/operator-stats` - Operator stats
- `/analytics/transport-patterns` - Transport detection
- `/analytics/user/{user_id}/travel-insights` - User analytics
- `/analytics/dashboard` - Admin dashboard

### Admin Endpoints
- `/admin/routes/refresh` - Refresh route cache
- `/admin/routes/status` - Cache status

## Prerequisites

- Python 3.8+
- Required packages (see `requirements.txt`):
    - FastAPI
    - Uvicorn
    - SQLModel
    - Passlib
    - PyOTP
    - Shapely
    - Other dependencies

## Getting Started

### Local Development Setup

1. Clone the repository:
     ```bash
     git clone https://github.com/owohappy/traveltime-backend.git
     cd traveltime-backend
     ```

2. Create a virtual environment:
     ```bash
     python -m venv venv
     source venv/bin/activate  # On Windows: venv\Scripts\activate
     ```

3. Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```

4. Run the application:
     ```bash
     uvicorn main:app --reload
     ```

### Docker Setup

1. Build and start the containers:
     ```bash
     docker-compose up --build
     ```

2. Access the application at `http://localhost:8000`

### Production Deployment

#### Option 1: Automated Deployment (Recommended)
```bash
# Complete production deployment with SSL setup
./deploy_production.sh
```

#### Option 2: Manual Docker Setup
1. Copy environment variables:
     ```bash
     cp .env.example .env
     # Edit .env with your production values
     ```

2. Set up SSL certificates (for HTTPS):
     ```bash
     # Option A: Automated SSL setup
     ./setup_ssl.sh
     
     # Option B: Manual certificate placement
     # Place your certificate files in ssl/cert.pem and ssl/key.pem
     ```

3. Build and start services:
     ```bash
     docker-compose up -d --build
     ```

4. Verify deployment:
     ```bash
     # Test SSL and services
     ./test_ssl.sh
     
     # Or manual testing
     curl https://tt.owohappy.com/ping
     ```

#### SSL Configuration

The production deployment includes full SSL support:
- **Automatic HTTPS redirect** from HTTP (port 80) to HTTPS (port 443)
- **Modern SSL/TLS configuration** with strong ciphers
- **Security headers** including HSTS, CORS, and anti-clickjacking
- **Let's Encrypt support** for free, automated certificates
- **Certificate auto-renewal** with monitoring

**SSL Setup Options:**
1. **Let's Encrypt** (Recommended): Free, automated, trusted certificates
2. **Self-signed**: For testing only, shows browser warnings
3. **Commercial certificates**: Upload your own certificates

**SSL Scripts:**
- `./setup_ssl.sh` - Interactive SSL certificate setup
- `./renew_ssl.sh` - Automatic certificate renewal
- `./test_ssl.sh` - Comprehensive SSL testing

#### Production URLs
- **HTTPS**: https://tt.owohappy.com (Secure, recommended)
- **HTTP**: http://tt.owohappy.com (Redirects to HTTPS)
- **API Health**: https://tt.owohappy.com/ping

#### Legacy Production Script
```bash
# Simple production start (no SSL setup)
./start_production.sh
```

## Testing

### Test Scripts
- **Analytics Tests**: `python test_analytics_api.py` - Test all analytics endpoints
- **GPS Tracking Tests**: `python test_gps_api.py` - Test GPS tracking functionality
- **Route Performance Tests**: `python test_route_performance.py` - Test route cache performance
- **Initialize Sample Data**: `python init_analytics_data.py` - Create sample analytics data

### Test Coverage
- Authentication and authorization
- GPS tracking and route detection
- Analytics endpoints and data processing
- Route cache management and performance
- Admin tools and monitoring endpoints

## Documentation

- **Complete API Documentation**: `COMPLETE_API_DOCUMENTATION.md` - Full API reference with all endpoints
- **SSL Setup Guide**: `SSL_SETUP_GUIDE.md` - SSL certificate setup and management
- **Analytics System**: `ANALYTICS_SYSTEM.md` - Analytics features and usage
- **Performance Improvements**: `PERFORMANCE_IMPROVEMENTS.md` - System optimizations
- **GPS Tracking**: `GPS_TRACKING.md` - GPS tracking documentation
- **Interactive Docs**: Available at `/docs` when running the server

## Production Operations

### Monitoring and Maintenance
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# SSL certificate status
openssl x509 -in ssl/cert.pem -noout -dates

# Run full system tests
./test_ssl.sh
```

### SSL Certificate Management
```bash
# Check certificate expiration
./renew_ssl.sh

# Set up automatic renewal (add to crontab)
0 2 * * * /path/to/backend-traveltime/renew_ssl.sh >> /var/log/ssl-renewal.log 2>&1
```

### Troubleshooting
```bash
# Reset database (careful!)
./reset_database.sh

# API verification
python api_verification.py

# Check deployment status
python check_deployment.py
```

## Project Structure

- **auth/**: Authentication and user management
- **routes/**: API route definitions (auth, account, travel, misc)
- **travel/**: Travel tracking and route verification with analytics
- **misc/**: Database models, configuration, and utilities
- **admin/**: Admin tools and user management
- **levels/**: XP calculation and user level management
- **gambling/**: Optional gambling features

## API Documentation

The API provides endpoints for:
- User authentication
- Account management
- Travel tracking
- Statistics and metrics

Complete API documentation is available at the `/docs` endpoint.

See `API.md` for detailed endpoint information.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.