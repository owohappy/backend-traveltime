from pydantic import BaseModel
from typing import Literal

class User(BaseModel):
    username: str
    hashed_password: str
    role: Literal["admin", "user", "moderator"]
