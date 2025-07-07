from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from auth.accountManagment import get_current_user
from misc import schemas, models, db
import auth

app = APIRouter(tags=["Authentication"])

@app.post("/register", 
          response_model=schemas.Token,
          status_code=status.HTTP_201_CREATED)
async def register(
    user: schemas.UserCreate,
    session: Session = Depends(db.get_session)
):
    return await auth.register(user, session)

@app.post("/login", response_model=schemas.Token)
async def login(
    credentials: schemas.UserLogin,
    session: Session = Depends(db.get_session)
):
    return await auth.login(credentials, session)

@app.post("/logout")
async def logout(token: str = Depends(schemas.oauth2_scheme)):
    return await auth.logout(token)

@app.post("/refresh-token",
          response_model=schemas.Token)
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

        if not payload:
            response.status_code = 404
            return {"valid": False, "error": "Token not found"}
        else:
            return {"valid": True}
    except Exception as e:
            return {"valid": False, "error": str(e)}

@app.post("/password-reset/initiate")
async def initiate_password_reset(
    email: str,
    session: Session = Depends(db.get_session)
):
    return await auth.initiate_password_reset(email, session) # type: ignore

@app.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: schemas.PasswordResetConfirm,
    session: Session = Depends(db.get_session)
):
    return await auth.confirm_password_reset(reset_data, session) # type: ignore

@app.get("/verify-email/{token}")
async def verify_email(
    token: str,
    session: Session = Depends(db.get_session)
):
    return await auth.verify_email(token, session) # type: ignore

@app.post("/resend-verification")
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
 