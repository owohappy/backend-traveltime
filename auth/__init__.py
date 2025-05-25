# All Functions
from datetime import datetime
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
            email.sendVerfyEmail(new_user.email, verification_token) # type: ignore
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
                          .where(models.User.email == credentials.email)).first() # type: ignore
        if not user or not verify_password(credentials.password, user[0].hashed_password):
            logging.log(f"Failed login attempt for {credentials.email}", "warning")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        if user[0].mfa:
            temp_token = create_temp_token({"sub": user[0].email + str("a")}) # type: ignore
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
        # Verify token first
        if not is_token_valid(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user info from token for logging purposes
        user_info = decode_access_token(token)
        
        # Blacklist the token
        blacklist_token(token)
        
        logging.log(f"User {user_info.get('sub', 'unknown')} logged out successfully", "info") # type: ignore
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
        user = session.exec(select(models.User).where(models.User.email == email)).first() # type: ignore
        if not user:
            # Still return success to prevent email enumeration
            return {"message": "If the email exists, reset instructions have been sent"}
        
        reset_token = create_verify_token(email)
        reset_url = f"{BASE_URL}/reset-password/{reset_token}"

        # Store reset token in database
        expiry = datetime.utcnow() + datetime.timedelta(hours=24) # type: ignore
        reset_record = models.PasswordResetToken(
            email=email, # type: ignore
            token=reset_token,
            expires_at=expiry
        )
        session.add(reset_record)
        session.commit()

        if not DEBUG:
            # Send actual email
            email.sendPasswordResetEmail(email, reset_url) # type: ignore
        else:
            # Log URL for debugging
            logging.log(f"Password reset URL: {reset_url}", "debug")
            
        return {"message": "Password reset instructions sent"}

    except Exception as e:
        session.rollback()
        logging.log(f"Password reset initiation error: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate password reset"
        )

async def confirm_password_reset(
    reset_data: schemas.PasswordReset,
    session: Session = Depends(db.get_session)
):
    """Finalize password reset with new password"""
    try:
        # Verify token
        token_record = session.exec(
            select(models.PasswordResetToken)
            .where(
                models.PasswordResetToken.token == reset_data.token, # type: ignore
                models.PasswordResetToken.used == False, # type: ignore
                models.PasswordResetToken.expires_at > datetime.utcnow() # type: ignore
            )
        ).first() # type: ignore
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Get user and update password
        user = session.exec(
            select(models.User)
            .where(models.User.email == token_record.email) # type: ignore
        ).first() # type: ignore
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password
        user.hashed_password = hash_password(reset_data.new_password) # type: ignore
        
        # Mark token as used
        token_record.used = True
        
        session.commit()
        
        # Log the event
        logging.log(f"Password reset completed for {user.email}", "info")
        
        return {"message": "Password has been reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logging.log(f"Password reset confirmation error: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
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
        current_user = session.exec(select(models.User).where(models.User.email == email)).first() # type: ignore
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
            email.sendVerfyEmail(current_user.email, verification_url) # type: ignore
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
                    .where(models.User.id == current_user.id) # type: ignore
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
        # Create a token revocation entry in the database
        revocation = models.TokenRevocation( # type: ignore
            user_id=current_user.id, # type: ignore
            revocation_time=datetime.utcnow() # type: ignore
        )
        
        session.add(revocation)
        session.commit()
        
        logging.log(f"All tokens revoked for user {current_user.email}", "info")
        return {"message": "All tokens have been revoked. Please log in again."}
    
    except Exception as e:
        session.rollback()
        logging.log(f"Token revocation error: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke tokens"
        )