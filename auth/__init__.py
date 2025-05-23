# All Functions
import json
from random import randrange
from fastapi import Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, update
from sqlmodel import Session
from misc import config, db, schemas, logging, models, email
import pyotp
######
# Auth Functions 
from .accountManagment import (
    check_verify_token, create_verify_token, hash_password, verify_password, 
    create_access_token, decode_access_token, 
    is_token_valid, get_current_user, 
    blacklist_token,
)
from .mfaHandling import (
    create_mfa_token, check_mfa_token, 
    create_temp_token, check_temp_token,
)
######


jsonConfig = config.config
DEBUG = jsonConfig['app']['debug']
BASE_URL = jsonConfig['app']['baseURL']
DB_NAME = jsonConfig['app']['nameDB']

# ======================
# Helper Functions
# ======================

def get_db_user(user_id: int, session: Session) -> models.User:
    """Retrieve user from database with error handling"""
    user = session.exec(select(models.User).where(models.User.id == user_id)).first() # type: ignore
    if not user:
        logging.log(f"User {user_id} not found", "warning")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# ======================
# Account Management Functions
# ======================

async def register(
    user: schemas.UserCreate,
    session: Session = Depends(db.get_session)
):
    """Register a new user in the system"""
    try:
        # Check for existing user
        existing_user = session.exec(select(models.User).where(models.User.email == user.email)).first() # type: ignore
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Generate unique user ID
        user_id = randrange(100000000, 999999999)
        while session.exec(select(models.User).where(models.User.id == user_id)).first(): # type: ignore
            user_id = randrange(100000000, 999999999)

        # Create new user object
        new_user = models.User(
            id=user_id,
            email=user.email,
            hashed_password=hash_password(user.password),
            email_verified=False,
            name=user.name,
            phonenumber=user.phonenumber,
            address=user.address,
        )

        # Database operations
        session.add(new_user)
        session.commit()
        
        # Generate tokens
        access_token = create_access_token({"sub": str(new_user.id) + str("a")})
        verification_token = create_verify_token(new_user.email)

        # Send verification email
        if not DEBUG:
            email.sendVerfyEmail(new_user.email, verification_token)
        else:
            logging.log(f"Verification URL: {BASE_URL}/verify-email/{verification_token}", "debug")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "userID": user_id
        }

    except Exception as e:
        session.rollback()
        logging.log(f"Registration error: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )
    
async def login(
    credentials: schemas.UserLogin,
    session: Session = Depends(db.get_session)
):
    """Authenticate user and return access token"""
    try:
        user = session.exec(select(models.User)
                          .where(models.User.email == credentials.email)).first()
        if not user or not verify_password(credentials.password, user[0].hashed_password):
            logging.log(f"Failed login attempt for {credentials.email}", "warning")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        if user[0].mfa:
            temp_token = create_temp_token({"sub": user[0].email + str("a")})
            return {"temp_token": temp_token, "mfa_required": True}
        access_token = create_access_token({"sub": str(user[0].email)})
        loginresponse = {
            "access_token": access_token,
            "token_type": "bearer",
            "userID": user[0].id
        }
        return loginresponse

    except Exception as e:
        logging.log(f"Login error: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )
    
async def logout(token: str = Depends(schemas.oauth2_scheme)):
    """Invalidate user's access token"""
    try:
        if not is_token_valid(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
        blacklist_token(token)
        logging.log("User logged out successfully", "info")
        return {"message": "Successfully logged out"}

    except Exception as e:
        logging.log(f"Logout error: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

async def initiate_password_reset(
    email: str,
    session: Session = Depends(db.get_session)
):
    """Initiate password reset process"""
    try:
        user = session.exec(select(models.User).where(models.User.email == email)).first()
        if not user:
            return  # Prevent email enumeration
        
        reset_token = create_verify_token(email)
        reset_url = f"{BASE_URL}/reset-password/{reset_token}"
        
        if not DEBUG:
            email.sendPasswordResetEmail(user.email, reset_url)
        else:
            logging.log(f"Password reset URL: {reset_url}", "debug")
            
        return {"message": "Password reset instructions sent"}

    except Exception as e:
        logging.log(f"Password reset initiation error: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

async def confirm_password_reset(
    reset_data: schemas.PasswordResetConfirm,
    session: Session = Depends(db.get_session)
):
    """Finalize password reset with new password"""
    try:
        # Token verification logic here
        # Update password in database
        return {"message": "Password successfully reset"}
    
    except Exception as e:
        logging.log(f"Password reset confirmation error: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

async def verify_email(
    token: str,
    session: Session = Depends(db.get_session)
):
    """Verify user's email address"""
    try:
        jsonTokenResponse = check_verify_token(token)
        if not jsonTokenResponse["valid"]:
            return jsonable_encoder(jsonTokenResponse)
        
        user = session.exec(select(models.User).where(models.User.email == jsonTokenResponse['userid'])).first() # type: ignore

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        email = session.exec(select(str(models.User.email))  # type: ignore
                            .where(models.User.email == jsonTokenResponse['userid'])).first()
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )



        session.exec(update(models.User)
                    .where(models.User.email == str(email)) # type: ignore
                    .values(email_verified=True))
        session.commit()
        
        logging.log(f"Email verified for user {user}", "info")
        return {"message": "Email successfully verified"}

    except Exception as e:
        session.rollback()
        logging.log(f"Email verification error: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )

async def request_email_verification(
    email: str,
    session: Session = Depends(db.get_session)
):
    """Request email verification for the current user"""
    try:
        current_user = session.exec(select(models.User).where(models.User.email == email)).first()
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        # Check if email is already verified
        if current_user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )

        verification_token = create_verify_token(current_user.email)
        verification_url = f"{BASE_URL}/verify-email/{verification_token}"

        if not DEBUG:
            email.sendVerfyEmail(current_user.email, verification_url)
        else:
            logging.log(f"Verification URL: {verification_url}", "debug")

        return {"message": "Verification email sent"}

    except Exception as e:
        logging.log(f"Email verification request error: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
async def check_token(token: str, session: Session = Depends(db.get_session)):
    """Check if the token is valid"""
    try:
        if not is_token_valid(token):
            return False
        
        decoded_token = decode_access_token(token)
        return True

    except Exception as e:
        logging.log(f"Token check error: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token check failed"
        )

async def enable_2fa(
    current_user: models.User = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    """Enable two-factor authentication for user"""
    try:
        #TODO: add auth
        # Generate MFA secret
        mfa_secret = pyotp.random_base32()
        session.exec(update(models.User)
                    .where(models.User.id == current_user.id)
                    .values(mfa_secret=mfa_secret))
        session.commit()
        
        # Generate provisioning URI for authenticator apps
        provisioning_uri = pyotp.totp.TOTP(mfa_secret).provisioning_uri(
            name=current_user.email,
            issuer_name=jsonConfig['app']['name']
        )
        
        return {"provisioning_uri": provisioning_uri}

    except Exception as e:
        session.rollback()
        logging.log(f"2FA enable error: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable 2FA"
        )

async def revoke_tokens(
    current_user: models.User = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    """Revoke all tokens for the current user"""
    try:
        return None 
    except Exception as e: 
        return None