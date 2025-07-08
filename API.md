# API Documentation

## Authentication

### Register
- **Endpoint:** `POST /register`
- **Body:** `UserCreate` schema
- **Description:** Create a new user account

### Login
- **Endpoint:** `POST /login`
- **Request Body:** `UserLogin` schema
- **Response:** `Token` schema
- **Description:** Authenticate user and receive an access token.
- **Codebase:** `auth/routes.py`

### Logout
- **Endpoint:** `POST /logout`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Invalidate the current access token.
- **Codebase:** `auth/routes.py`

### Refresh Token
- **Endpoint:** `POST /refresh-token`
- **Header:** `Authorization: Bearer <refresh_token>`
- **Response:** `Token` schema
- **Description:** Refresh access token using a refresh token.
- **Codebase:** `auth/token_handlers.py`

### Password Reset
- **Initiate:** `POST /password-reset/initiate`
  - **Body:** `{ "email": "<user_email>" }`
  - **Description:** Initiate password reset process by sending email.
- **Confirm:** `POST /password-reset/confirm`
  - **Body:** `PasswordResetConfirm` schema
  - **Description:** Confirm password reset with verification token.
- **Codebase:** `auth/password_reset.py`

### Email Verification
- **Endpoint:** `GET /verify-email/{token}`
- **Description:** Verify user's email address with token sent via email.
- **Codebase:** `auth/verification.py`

### Two-Factor Authentication
- **Enable:** `POST /2fa/enable`
  - **Header:** `Authorization: Bearer <token>`
  - **Description:** Enable two-factor authentication for user.
- **Verify:** `POST /2fa/verify`
  - **Body:** `MFAVerification` schema
  - **Response:** `Token` schema
  - **Description:** Verify 2FA code and receive an access token.
- **Codebase:** `auth/mfa.py`

---

## Account Management

### User Points
- **Endpoint:** `GET /user/{user_id}/points`
- **Header:** `Authorization: Bearer <token>`
- **Response:** `PointsResponse` schema
- **Description:** Get current points for a user with auth checks.
- **Codebase:** `routes/account.py`

### User Profile Management
- **Get Profile:** `GET /user/{user_id}/profile`
  - **Header:** `Authorization: Bearer <token>`
  - **Response:** User profile with personal info, travel stats, and achievements
  - **Description:** Get user profile with travel data and achievements.
- **Update Profile:** `PUT /user/{user_id}/profile`
  - **Header:** `Authorization: Bearer <token>`
  - **Body:** Form data with username, email, bio, privacy_settings
  - **Description:** Update user profile information with validation.
- **Codebase:** `routes/account.py`

### Profile Picture Management
- **Upload Picture:** `POST /user/{user_id}/picture`
  - **Header:** `Authorization: Bearer <token>`
  - **Body:** Multipart form with image file
  - **Description:** Upload and process profile picture with image validation, optimization, and resizing.
- **Get Picture:** `GET /user/{user_id}/picture`
  - **Description:** Retrieve user profile picture with fallback to default image.
- **Codebase:** `routes/account.py`

### User Achievements
- **Endpoint:** `GET /user/{user_id}/achievements`
- **Header:** `Authorization: Bearer <token>`
- **Response:** User achievements and badges based on travel activity
- **Description:** Get user achievements calculated from points, travel time, and trip statistics.
- **Codebase:** `routes/account.py`

### User Preferences
- **Get Preferences:** `GET /user/{user_id}/preferences`
  - **Header:** `Authorization: Bearer <token>`
  - **Response:** User preferences and settings
  - **Description:** Get user preferences including notifications, privacy, and app settings.
- **Update Preferences:** `PUT /user/{user_id}/preferences`
  - **Header:** `Authorization: Bearer <token>`
  - **Body:** JSON object with preference updates
  - **Description:** Update user preferences and settings.
- **Codebase:** `routes/account.py`

### Legacy Endpoints (Backward Compatibility)
- **Get User Data:** `GET /user/{user_id}/getData`
  - **Header:** `Authorization: Bearer <token>`
  - **Description:** Legacy endpoint - use `/user/{user_id}/profile` instead.
- **Get User Hours:** `GET /user/{user_id}/getDataHours`
  - **Header:** `Authorization: Bearer <token>`
  - **Description:** Legacy endpoint for user hours data.
- **Codebase:** `routes/account.py`

---

## Travel Tracking

### GPS Location Tracking (Enhanced)
- **Endpoint:** `POST /gps/track/{user_id}`
- **Body:** `LocationPing` schema (enhanced with accuracy, altitude, speed, bearing)
- **Header:** `Authorization: Bearer <token>`
- **Description:** Primary GPS tracking endpoint for monitoring public transport usage. Tracks travel sessions, calculates duration/distance, awards XP, and detects transport type.
- **Response:** Detailed travel status, session info, location data, rewards, and daily stats
- **Codebase:** `routes/travel.py`, `travel/__init__.py`

### GPS Tracking Status
- **Endpoint:** `GET /gps/status/{user_id}`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Get current tracking status without submitting new location data. Returns active session info and travel statistics.
- **Response:** Current session status, travel statistics (daily/weekly/monthly), user profile
- **Codebase:** `routes/travel.py`

### Nearby Routes Discovery
- **Endpoint:** `GET /gps/routes/nearby?latitude={lat}&longitude={lon}&radius={meters}`
- **Query Params:** `latitude`, `longitude`, `radius` (optional, max 5000m)
- **Header:** `Authorization: Bearer <token>`
- **Description:** Discover nearby public transportation routes and check transport availability.
- **Response:** Route analysis, transport type detection, nearby routes list
- **Codebase:** `routes/travel.py`, `travel/__init__.py`

### Heartbeat (Legacy)
- **Endpoint:** `POST /heartbeat/{user_id}`
- **Body:** `LocationPing` schema
- **Header:** `Authorization: Bearer <token>`
- **Description:** Legacy GPS ping endpoint. **DEPRECATED** - use `/gps/track/{user_id}` instead.
- **Codebase:** `routes/travel.py`

### Travel Confirmation
- **Endpoint:** `POST /user/{user_id}/confirm_travel/{travel_id}`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Confirm travel with proof (future feature).
- **Codebase:** `travel/confirmation.py`

---

## Statistics and Metrics

### System Statistics
- **Users Count:** `GET /stats/users_count`
  - **Description:** Get total number of registered users.
- **Points Total:** `GET /stats/points_total`
  - **Description:** Get total points earned by all users.
- **Codebase:** `stats/metrics.py`

### User Leaderboard
- **Endpoint:** `GET /stats/leaderboard`
- **Description:** Get top 10 users by points.
- **Response:** `LeaderboardResponse` schema
- **Codebase:** `stats/leaderboard.py`

### Health Check
- **Endpoint:** `GET /ping`
- **Description:** Health check endpoint.
- **Codebase:** `core/health.py`

---

## Analytics and Insights

### Popular Routes Analytics
- **Endpoint:** `GET /analytics/popular-routes?limit={number}`
- **Query Params:** `limit` (optional, default: 10, max: 50)
- **Header:** `Authorization: Bearer <token>`
- **Description:** Get most popular transportation routes based on usage analytics.
- **Response:** Popular routes list with usage statistics, route details, and confidence scores.
- **Codebase:** `routes/travel.py`

### Operator Statistics
- **Endpoint:** `GET /analytics/operator-stats`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Get operator stats including market share and transport types.
- **Response:** Operator analytics with route counts, transport types, and market share percentages.
- **Codebase:** `routes/travel.py`

### Transport Pattern Analytics
- **Endpoint:** `GET /analytics/transport-patterns`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Get learned transport patterns and type detection analytics including speed profiles and confidence scores.
- **Response:** Transport patterns with detection accuracy, learning statistics, and confidence metrics.
- **Codebase:** `routes/travel.py`

### User Travel Insights
- **Endpoint:** `GET /analytics/user/{user_id}/travel-insights`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Get personalized travel insights and analytics for a specific user including travel patterns, preferences, and efficiency metrics.
- **Response:** User travel analytics with patterns and preferences.
- **Codebase:** `routes/travel.py`

### Analytics Dashboard
- **Endpoint:** `GET /analytics/dashboard`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Get analytics dashboard for admin monitoring.
- **Response:** Analytics dashboard with system metrics and route stats.
- **Codebase:** `routes/travel.py`

---

## Admin Operations

### Route Cache Refresh
- **Endpoint:** `POST /admin/routes/refresh`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Force refresh of transportation route cache from all configured APIs.
- **Response:** Cache refresh status with duration and route count.
- **Codebase:** `routes/travel.py`

### Route Cache Status
- **Endpoint:** `GET /admin/routes/status`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Get detailed route cache status and performance metrics.
- **Response:** Cache status, route manager statistics, and performance metrics.
- **Codebase:** `routes/travel.py`

---

## Notes

- All endpoints requiring authentication expect a JWT Bearer token in the `Authorization` header.
- Request/response schemas are defined in `schemas/` directory.
- API error responses follow standard HTTP status codes with a consistent format.
- Rate limiting may apply to certain endpoints.
- Complete API swagger documentation available at `/docs` endpoint.