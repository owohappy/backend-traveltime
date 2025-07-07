from datetime import datetime, timedelta
import string
import random
from misc import db, logging, config
from sqlmodel import Session, select
from misc import models
import secrets
from jose import jwt

temp_tokens = []

cfg = config.config
try:
    SECRET_KEY = cfg['security']['jwtSecret']
except KeyError:
    SECRET_KEY = cfg['app']['jwtSecretKey']

def create_mfa_token(user_id, session):
    token = secrets.token_hex(32)
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    mfa_token = models.MFAToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    
    session.add(mfa_token)
    session.commit()
    return token

def check_mfa_token(token, user_id, session):
    try:
        db_token = session.exec(
            select(models.MFAToken)
            .where(
                models.MFAToken.token == token,
                models.MFAToken.user_id == user_id,
                models.MFAToken.used == False,
                models.MFAToken.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not db_token:
            return False
        
        db_token.used = True
        session.commit()
        return True
    
    except Exception as e:
        logging.log(f"MFA check error: {e}", "error")
        return False

def create_temp_token(data):
    expire = datetime.utcnow() + timedelta(minutes=10)
    data.update({"exp": expire.timestamp()})
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")

def check_temp_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        if "exp" not in payload or datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
            return {"valid": False, "error": "Token expired"}
        
        return {"valid": True, "payload": payload}
    
    except jwt.PyJWTError as e:
        logging.log(f"Temp token error: {e}", "error")
        return {"valid": False, "error": str(e)}