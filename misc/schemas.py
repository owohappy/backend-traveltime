from pydantic import BaseModel, EmailStr
from typing import Optional
import time 
# === Pydantic Schemas ===
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    username: str
    phonenumber: str
    address: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    userID: Optional[int]

class LocationPing(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    timestamp: Optional[str] = None  # ISO format 
    accuracy: Optional[float] = None 
    altitude: Optional[float] = None  
    speed: Optional[float] = None  # m/s
    bearing: Optional[float] = None  

class oauth2_scheme(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
    mfa_code: str
    grant_type: str = "authorization_code"
    scope: Optional[str] = None

class PasswordReset(BaseModel):
    email: EmailStr
    password: str
    token: str
    timestamp: str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    token: str
    timestamp: str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class MFAVerification(BaseModel):
    user_id: str
    mfa_code: str
    timestamp: str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

# Gambling Schemas
class GambleGameCreate(BaseModel):
    bet_amount: float

class GambleGameAction(BaseModel):
    game_id: str
    action: str  # "hit", "stand", "double_down"

class GambleGame(BaseModel):
    game_id: str
    player_cards: list
    dealer_cards: list
    bet_amount: float
    status: str  # "active", "won", "lost", "push"
    player_total: int
    dealer_total: int