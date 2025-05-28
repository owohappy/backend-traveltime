from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from auth.accountManagment import get_current_user
from misc import schemas, models, db
import auth

app = APIRouter(tags=["Authentication"])

# ======================
# Core Authentication Routes
# ======================

@app.post("/register", 
          response_model=schemas.Token,
          status_code=status.HTTP_201_CREATED,
          summary="Register a new user",
          description="Creates a new user account and returns an access token")
async def register(
    user: schemas.UserCreate,
    session: Session = Depends(db.get_session)
):
    """Register a new user in the system"""
    return await auth.register(user, session) # type: ignore





@app.post("/login",
          response_model=schemas.Token,
          summary="User login",
          description="Authenticates user credentials and returns tokens")
async def login(
    credentials: schemas.UserLogin,
    session: Session = Depends(db.get_session)
):
    """Authenticate user and return access token"""
    return await auth.login(credentials, session) # type: ignore



@app.post("/logout",
          summary="User logout",
          description="Invalidates the current access token")
async def logout(token: str = Depends(schemas.oauth2_scheme)):
    """Invalidate user's access token"""
    return await auth.logout(token)



# ======================
# Token Refresh
# ======================
@app.post("/refresh-token",
          response_model=schemas.Token,
          summary="Refresh access token",
          description="Generates a new access token using the refresh token")
async def refresh_token(
    token: str = Depends(schemas.oauth2_scheme),
    session: Session = Depends(db.get_session)
):
    """Refresh access token using refresh token"""
    return await auth.refresh_token(token, session) # type: ignore

@app.post("/check-token", 
            summary="Check token validity",
            description="Validates the provided access token")
async def check_token(
    response: Response,
    access_token: schemas.Token = Depends(schemas.Token),
    session: Session = Depends(db.get_session)
):
    """Check if the provided access token is valid"""
    try:
        payload = await auth.check_token(access_token.access_token)
        print("Payload:", payload)
        if not payload:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {"valid": False, "error": "Token not found"}
        else:
            return {"valid": True}
    except Exception as e:
            return {"valid": False, "error": str(e)}

# ======================
# Password Management
# ======================
@app.post("/password-reset/initiate",
          summary="Initiate password reset",
          description="Sends password reset instructions to registered email")
async def initiate_password_reset(
    email: str,
    session: Session = Depends(db.get_session)
):
    """Initiate password reset process"""
    return await auth.initiate_password_reset(email, session) # type: ignore



@app.post("/password-reset/confirm",
          summary="Confirm password reset",
          description="Complete password reset process with verification token")
async def confirm_password_reset(
    reset_data: schemas.PasswordResetConfirm,
    session: Session = Depends(db.get_session)
):
    """Finalize password reset with new password"""
    return await auth.confirm_password_reset(reset_data, session) # type: ignore


# ======================
# Email Verification
# ======================

@app.get("/verify-email/{token}",
         summary="Verify email address",
         description="Confirm user's email address using verification token")
async def verify_email(
    token: str,
    session: Session = Depends(db.get_session)
):
    """Verify user's email address"""
    return await auth.verify_email(token, session) # type: ignore


@app.post("/resend-verification",
          summary="Resend email verification",
          description="Sends a new verification email to the user")
async def resend_verification(
    email: str,
    session: Session = Depends(db.get_session)
):
    """Resend email verification link to user"""
    return await auth.request_email_verification(email, session) # type: ignore
 



# ======================
# Two-Factor Authentication
# ======================

@app.post("/2fa/enable",
          summary="Enable 2FA",
          description="Initiate two-factor authentication setup process")
async def enable_2fa(
    current_user: models.User = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    """Enable two-factor authentication for user"""
    return await auth.enable_2fa(current_user, session) # type: ignore
 


@app.post("/2fa/verify",
          response_model=schemas.Token,
          summary="Verify 2FA code",
          description="Validate two-factor authentication code")
async def verify_2fa(
    verification: schemas.MFAVerification,
    session: Session = Depends(db.get_session)
):
    """Verify MFA code and return access token"""
    return await auth.verify_2fa(verification, session) # type: ignore
 