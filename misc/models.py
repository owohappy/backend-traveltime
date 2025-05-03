from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional
from datetime import datetime 
# === Database Model ===
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)