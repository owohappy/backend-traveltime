from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import decode
from .schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    try:
        payload = decode(token)
        return TokenData(sub=payload["sub"], role=payload["role"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def require_role(required_role: str):
    def role_checker(user: TokenData = Depends(get_current_user)):
        if user.role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return user
    return role_checker
