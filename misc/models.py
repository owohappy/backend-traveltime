from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional
from datetime import datetime 
# === Database Model ===
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=320)  # 320 is max per spec
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    email_verified: bool
    name: Optional[str] = Field(default=None, max_length=100)
    phonenumber: Optional[str]
    address: Optional[str]
    email_verified_at: Optional[datetime] = Field(default=None)

class UserPoints(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    points: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})

