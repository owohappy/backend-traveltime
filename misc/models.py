from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime 
# === Database Model ===
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=320)  # 320 is max per spec
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    email_verified: bool
    pfp_url: Optional[str] = Field(default=None, max_length=300)
    name: Optional[str] = Field(default=None, max_length=100)
    phonenumber: Optional[str]
    address: Optional[str]
    email_verified_at: Optional[datetime] = Field(default=None)
    mfa: bool = Field(default=False)
    mfa_secret: Optional[str] = Field(default=None, max_length=100)
    type: str = Field(default="user")
    points: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    xp: int = Field(default=0)
    level: int = Field(default=0)
    

class UserPoints(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    points: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})

class TravelHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    startLatitude: float
    listLatitude: list
    startLongitude: float
    listLongitude: list
    distance: float
    duration: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    