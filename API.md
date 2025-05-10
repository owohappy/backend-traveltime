# API Documentation

## Authentication

### Register
- **POST** `/register`
- **Request Body:** `UserCreate`
- **Response:** `Token`
- **Description:** Register a new user and receive an access token.

### Login
- **POST** `/login`
- **Request Body:** `UserLogin`
- **Response:** `Token`
- **Description:** Authenticate user and receive an access token.

### Logout
- **POST** `/logout`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Invalidate the current access token.

### Refresh Token
- **POST** `/refresh-token`
- **Header:** `Authorization: Bearer <refresh_token>`
- **Response:** `Token`
- **Description:** Refresh access token using a refresh token.

### Password Reset Initiate
- **POST** `/password-reset/initiate`
- **Body:** `{ "email": "<user_email>" }`
- **Description:** Initiate password reset process.

### Password Reset Confirm
- **POST** `/password-reset/confirm`
- **Body:** `PasswordResetConfirm`
- **Description:** Confirm password reset with verification token.

### Email Verification
- **GET** `/verify-email/{token}`
- **Description:** Verify user's email address.

### Enable 2FA
- **POST** `/2fa/enable`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Enable two-factor authentication for user.

### Verify 2FA
- **POST** `/2fa/verify`
- **Body:** `MFAVerification`
- **Response:** `Token`
- **Description:** Verify 2FA code and receive an access token.

---

## Account

### Get User Points
- **GET** `/user/{user_id}/points`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Get current points for a user.

### Get User Data
- **GET** `/user/{user_id}/getData`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Get user profile data.

### Update User Data
- **POST** `/user/{user_id}/updateData`
- **Headers:**  
  - `field: <field_name>`  
  - `data: <new_value>`  
  - `Authorization: Bearer <token>`
- **Description:** Update user profile data.

---

## Travel

### Heartbeat (GPS Location)
- **POST** `/heartbeat/{user_id}`
- **Body:** `LocationPing`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Send GPS ping to estimate current route.

### Confirm Travel
- **POST** `/user/{user_id}/confirm_travel/{travel_id}`
- **Header:** `Authorization: Bearer <token>`
- **Description:** Confirm travel with proof (future feature).

---

## Miscellaneous

### Users Count
- **GET** `/stats/users_count`
- **Description:** Get total number of registered users.

### Points Total
- **GET** `/stats/points_total`
- **Description:** Get total points earned by all users.

### Leaderboard
- **GET** `/stats/leaderboard`
- **Description:** Get top 10 users by points.

### Ping
- **GET** `/ping`
- **Description:** Health check endpoint.

---

## Notes

- All endpoints requiring authentication expect a JWT Bearer token in the `Authorization` header.
- Request/response schemas are defined in [misc/schemas.py](misc/schemas.py).