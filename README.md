# TravelTime

An app that rewards users for taking public transportation instead of cars. The backend API tracks user travel routes and awards points for eco-friendly transportation choices.

## Features

- **Authentication**: User registration, login, logout, token refresh, and two-factor authentication
- **Account Management**: User profiles and points tracking
- **Travel Tracking**: GPS location monitoring to verify public transport usage
- **Route Management**: Advanced route caching with spatial indexing and multi-API integration
- **Analytics System**: Comprehensive travel analytics with ML-based transport type detection
- **Performance Optimization**: Lazy loading, caching, and grid-based spatial indexing
- **Statistics & Metrics**: Leaderboards and usage statistics
- **Admin Tools**: Route cache management and system monitoring
- **Gambling**: Optional point gambling with card games (Blackjack)

## Analytics Features

### Route Analytics
- **Popular Routes**: Track most used transportation routes
- **Operator Statistics**: Market share and transport type distribution
- **Transport Pattern Learning**: ML-based transport type detection
- **User Travel Insights**: Personalized travel analytics and recommendations
- **Analytics Dashboard**: Comprehensive system overview and monitoring

### API Endpoints
- `/analytics/popular-routes` - Get most popular routes
- `/analytics/operator-stats` - Operator statistics and market share
- `/analytics/transport-patterns` - ML transport type detection patterns
- `/analytics/user/{user_id}/travel-insights` - Personal travel analytics
- `/analytics/dashboard` - Complete analytics dashboard

### Admin Endpoints
- `/admin/routes/refresh` - Force refresh route cache
- `/admin/routes/status` - Route cache status and performance metrics

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

1. Copy environment variables:
     ```bash
     cp .env.example .env
     # Edit .env with your production values
     ```

2. Build for production:
     ```bash
     docker-compose up -d --build
     ```

3. Or run with production script:
     ```bash
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

- **API Documentation**: `API.md` - Complete API reference
- **Analytics System**: `ANALYTICS_SYSTEM.md` - Analytics features and usage
- **Performance Improvements**: `PERFORMANCE_IMPROVEMENTS.md` - System optimizations
- **GPS Tracking**: `GPS_TRACKING.md` - GPS tracking implementation
- **Interactive Docs**: Available at `/docs` when running the server

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