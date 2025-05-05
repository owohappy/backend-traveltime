from pydantic import BaseModel, EmailStr
from typing import Optional
import time 
# === Pydantic Schemas ===
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phonenumber: str
    address: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LocationPing(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    timestamp: str