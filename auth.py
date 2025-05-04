# auth.py
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
import string
import random
# === Password Hashing ===
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
verifyTokens = []

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# === JWT Handling ===
SECRET_KEY = "your_super_secret_key_here"  # Set a real secret!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

blacklisted_tokens = set()  # ⬅️ Add in-memory blacklist

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    if token in blacklisted_tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def is_token_valid(token: str) -> bool:
    try:
        decode_access_token(token)  
        return True  
    except HTTPException:
        return False

# === Current User Dependency ===
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    payload = decode_access_token(token)
    return payload.get("sub")

def blacklist_token(token: str):
    blacklisted_tokens.add(token)


def create_verify_token(userid: str):
    characters = string.ascii_letters + string.digits  # a-zA-Z0-9
    verify = ''.join(random.choices(characters, k=18))  
    verifyTokens.append({"userid":userid, "verifytoken": verify, "exp": datetime.now() + timedelta(seconds=600)})
    return verify


def check_email_token(userid: str, token: str):
    now = datetime.now()
    for entry in verifyTokens:
        if entry["userid"] == userid and entry["verifytoken"] == token:
            if now <= entry["exp"]:
                return {"valid": True}
            else:
                return {"valid": False, "reason": "The link has already expired"}  
    return {"valid": False, "reason": "The link can't be found in our database"}

