from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
import jwt
from .schemas import LoginRequest, Token
from .models import User
from db.user_repo import UserRepository

router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

user_repo = UserRepository(db_url="mongodb://localhost:27017", db_name="edupay")

@router.post("/login", response_model=Token)
async def login(data: LoginRequest):
    user = await user_repo.authenticate_user(data.username, data.password)
    if user:
        token = jwt.generate_user_token(user)
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/register", response_model=Token)
async def register(data: LoginRequest):
    if await user_repo.get_user(data.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    user = await user_repo.create_user(data.username, data.password)
    token = jwt.generate_user_token(user)
    return {"access_token": token, "token_type": "bearer"}


