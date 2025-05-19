# API Documentation

## Authentication

### Register
- **Endpoint:** `POST /register`
- **Request Body:** `UserCreate` schema
- **Note:** The references to "auth/token_handlers.py", "auth/password_reset.py", "auth/verification.py", "auth/mfa.py", "travel/confirmation.py", and "stats/metrics.py" in this documentation do not match the actual file structure. The related implementations reside in "routes/auth.py", "auth/accountManagment.py", "auth/mfaHandling.py", "routes/travel.py", and "routes/misc.py", respectively.
- **Description:** Register a new user and receive an access token.
- **Codebase:** `auth/routes.py`

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
- **Description:** Get current points for a user.
- **Codebase:** `user/points.py`

### User Profile
- **Get Profile:** `GET /user/{user_id}/getData`
  - **Header:** `Authorization: Bearer <token>`
  - **Response:** `UserProfile` schema
  - **Description:** Get user profile data.
- **Update Profile:** `POST /user/{user_id}/updateData`
  - **Headers:**  
    - `field: <field_name>`  
    - `data: <new_value>`  
    - `Authorization: Bearer <token>`
  - **Description:** Update user profile data.
- **Codebase:** `user/profile.py`

---

## Travel Tracking

### Heartbeat (GPS Location)
- **Endpoint:** `POST /heartbeat/{user_id}`
- **Body:** `LocationPing` schema
- **Header:** `Authorization: Bearer <token>`
- **Description:** Send GPS ping to estimate current route.
- **Codebase:** `travel/tracking.py`

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

## Implementation Notes

- All endpoints requiring authentication expect a JWT Bearer token in the `Authorization` header.
- Request/response schemas are defined in `schemas/` directory.
- API error responses follow standard HTTP status codes with a consistent format.
- Rate limiting may apply to certain endpoints.
- Complete API swagger documentation available at `/docs` endpoint.