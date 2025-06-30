# TravelTime

An app that rewards users for taking public transportation instead of cars. The backend API tracks user travel routes and awards points for eco-friendly transportation choices.

## Features

- **Authentication**: User registration, login, logout, token refresh, and two-factor authentication
- **Account Management**: User profiles and points tracking
- **Travel Tracking**: GPS location monitoring to verify public transport usage
- **Statistics & Metrics**: Leaderboards and usage statistics
- **Gambling**: Optional point gambling with card games (Blackjack)

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

## Project Structure

- **auth/**: Authentication and user management
- **routes/**: API route definitions (auth, account, travel, misc)
- **travel/**: Travel tracking and route verification
- **gambling/**: Point gambling functionality
- **misc/**: Utilities, schemas, templates
- **main.py**: Application entry point
- **API.md**: API documentation

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