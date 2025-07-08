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
- **GPS Tracking**: `GPS_TRACKING.md` - GPS tracking docs
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