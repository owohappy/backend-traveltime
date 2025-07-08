from sqlmodel import SQLModel, Field, Column
from typing import List, Optional
from datetime import datetime 
from sqlalchemy.dialects.sqlite import JSON

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=320)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    email_verified: bool = Field(default=False)
    pfp_url: Optional[str] = Field(default=None, max_length=300)
    name: Optional[str] = Field(default=None, max_length=100)
    phonenumber: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    email_verified_at: Optional[datetime] = Field(default=None)
    mfa: bool = Field(default=False)
    mfa_secret: Optional[str] = Field(default=None, max_length=100)
    type: str = Field(default="user")
    points: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    xp: int = Field(default=0)
    level: int = Field(default=0)

class UserHours(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    # General hours
    hoursTotal: float = Field(default=0)
    hoursWeekly: float = Field(default=0)
    hoursMonthly: float = Field(default=0)
    hoursDaily: float = Field(default=0)
    
    # Bus transport hours
    bus_hoursTotal: float = Field(default=0)
    bus_hoursWeekly: float = Field(default=0)
    bus_hoursMonthly: float = Field(default=0)
    bus_hoursDaily: float = Field(default=0)
    
    # Train transport hours
    train_hoursTotal: float = Field(default=0)
    train_hoursWeekly: float = Field(default=0)
    train_hoursMonthly: float = Field(default=0)
    train_hoursDaily: float = Field(default=0)
    
    # Ferry transport hours
    ferry_hoursTotal: float = Field(default=0)
    ferry_hoursWeekly: float = Field(default=0)
    ferry_hoursMonthly: float = Field(default=0)
    ferry_hoursDaily: float = Field(default=0)


class TravelHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    startLatitude: float
    # Store lists as JSON instead of raw list
    listLatitude: Optional[List[float]] = Field(sa_column=Column(JSON))
    startLongitude: float
    listLongitude: Optional[List[float]] = Field(sa_column=Column(JSON))
    distance: float
    duration: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PasswordResetToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    token: str = Field(unique=True, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow().replace(hour=23, minute=59, second=59))
    used: bool = Field(default=False)  # Track if the token has been used

class MFAToken(SQLModel, table=True):
    """Table for storing MFA tokens"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    used: bool = Field(default=False)

class TempToken(SQLModel, table=True):
    """Table for storing temporary tokens (e.g., for MFA process)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    used: bool = Field(default=False)

class TokenRevocation(SQLModel, table=True):
    """Table for storing token revocation information"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    revocation_time: datetime