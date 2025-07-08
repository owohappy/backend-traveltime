import json
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
import string
import misc
import random
from misc import config
from misc import schemas
import misc.logging

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
verify_tokens = []  # TODO: move to redis

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT setup
config_data = config.config
SECRET_KEY = config_data['app']['jwtSecretKey']
if not SECRET_KEY:
    SECRET_KEY = "your_super_secret_key_here"
    misc.logging.log("Using default JWT key - change this!", "warning")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

blacklisted_tokens = set()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    if token in blacklisted_tokens:
        return False
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return False

def is_token_valid(token: str) -> bool:
    try:
        return decode_access_token(token) is not False
    except HTTPException:
        return False

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

def blacklist_token(token: str):
    blacklisted_tokens.add(token)

def create_verify_token(userid: str):
    chars = string.ascii_letters + string.digits
    verify = ''.join(random.choices(chars, k=18))  
    verify_tokens.append({"userid":userid, "verifytoken": verify})
    return verify

def check_verify_token(token: str):
    for entry in verify_tokens:
        if entry["verifytoken"] == token:
            return {"valid": True, "userid": entry["userid"]}
    return {"valid": False, "reason": "Token not found"}

def create_reset_token(userid: str):
    chars = string.ascii_letters + string.digits
    verify = ''.join(random.choices(chars, k=18))  
    verify_tokens.append({"userid":userid, "verifytoken": verify, "exp": datetime.now() + timedelta(seconds=1800)})
    return verify

def check_reset_token(userid: str, token: str):
    now = datetime.now()
    for entry in verify_tokens:
        if entry["userid"] == userid and entry["verifytoken"] == token:
            if entry.get("exp") < now:
                return {"valid": False, "reason": "Token expired"}
            return {"valid": True}
    return {"valid": False, "reason": "Token not found"}
