from random import random
from datetime import datetime, timedelta
import datetime as dt
import string
from misc import db
import datetime
from sqlmodel import Session, select
from misc import models, db, logging
import secrets
import jwt
from misc import config


tempTokens = []

jsonConfig = config.config
SECRET_KEY = jsonConfig['security']['jwtSecret']
TEMP_TOKEN_EXPIRE_MINUTES = 10
MFA_TOKEN_EXPIRE_MINUTES = 5


def add_mfa_token(userid: str, token: str):
    """
    Adds a new MFA token for the user.
    If the user already has an MFA token, it will be replaced.
    """
    now = dt.datetime.now()
    #create an sql; db
    db.execute("INSERT INTO mfaTokens (userid, mfatoken, created_at) VALUES (?, ?, ?)", (userid, token, now))  # type: ignore
    db.commit()  # type: ignore                                                                                                                                                                                                                                          
    

    return {"valid": True, "reason": "MFA token created"}

def check_mfa(userid: str):
    now = dt.datetime.now()
    result = db.execute("SELECT * FROM mfaTokens WHERE userid = ? AND created_at > ?", (userid, now - timedelta(minutes=5)))  # type: ignore
    return {"valid": bool(result), "reason": "MFA token is valid" if result else "MFA token is invalid"}

def create_mfa_token(userid: str): # type: ignore
    characters = string.ascii_letters + string.digits  # a-zA-Z0-9
    verify = ''.join(random.choices(characters, k=18))   # type: ignore
    add_mfa_token(userid, verify)
    return verify

def check_mfa_token(userid: str, token: str): # type: ignore
    now = dt.datetime.now()
    result = db.execute("SELECT * FROM mfaTokens WHERE userid = ? AND mfatoken = ? AND created_at > ?", (userid, token, now - timedelta(minutes=5)))  # type: ignore
    return {"valid": bool(result), "reason": "MFA token is valid" if result else "MFA token is invalid"}



# Tokens to handle MFA login
def create_temp_token(userid: str): # type: ignore
    characters = string.ascii_letters + string.digits  # a-zA-Z0-9
    verify = ''.join(random.choices(characters, k=18))   # type: ignore
    tempTokens.append({"userid":userid, "temptoken": verify, "exp": dt.datetime.now() + timedelta(seconds=300)})
    return verify

def check_temp_token(userid: str, token: str): # type: ignore
    now = dt.datetime.now()
    for entry in tempTokens:
        if entry["userid"] == userid and entry["temptoken"] == token:
            return {"valid": True}
    return {"valid": False, "reason": "The link can't be found in our database"}


def create_mfa_token(user_id: int, session: Session) -> str:
    """Create and store MFA token in database"""
    token = secrets.token_hex(32)
    expires_at = dt.datetime.utcnow() + dt.timedelta(minutes=MFA_TOKEN_EXPIRE_MINUTES)
    
    # Store in database
    mfa_token = models.MFAToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    
    session.add(mfa_token)
    session.commit()
    
    return token

def check_mfa_token(token: str, user_id: int, session: Session) -> bool:
    """Verify MFA token from database"""
    try:
        # Find token in database
        db_token = session.exec(
            select(models.MFAToken)
            .where(
                models.MFAToken.token == token,
                models.MFAToken.user_id == user_id,
                models.MFAToken.used == False,
                models.MFAToken.expires_at > datetime.datetime.utcnow()
            )
        ).first()
        
        if not db_token:
            return False
        
        # Mark token as used
        db_token.used = True
        session.commit()
        
        return True
    
    except Exception as e:
        logging.log(f"MFA token check error: {str(e)}", "error")
        return False

def create_temp_token(data: dict) -> str:
    """Create temporary token for MFA process"""
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=TEMP_TOKEN_EXPIRE_MINUTES)
    data.update({"exp": expire.timestamp()})
    
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")

def check_temp_token(token: str) -> dict:
    """Verify temporary token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        # Check expiration
        if "exp" not in payload or datetime.datetime.fromtimestamp(payload["exp"]) < datetime.datetime.utcnow():
            return {"valid": False, "error": "Token expired"}
        
        return {"valid": True, "payload": payload}
    
    except jwt.PyJWTError as e:
        logging.log(f"Temp token verification error: {str(e)}", "error")
        return {"valid": False, "error": str(e)}