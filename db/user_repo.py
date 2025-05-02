from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic User Model
class User(BaseModel):
    username: str
    hashed_password: str
    role: str

class UserInDB(User):
    _id: Optional[str] = None

class UserRepository:
    def __init__(self, db_url: str, db_name: str):
        self.client = AsyncIOMotorClient(db_url)
        self.db = self.client[db_name]
        self.users = self.db["users"]

    async def get_user(self, username: str) -> Optional[UserInDB]:
        user_data = await self.users.find_one({"username": username})
        if user_data:
            return UserInDB(**user_data)
        return None

    async def create_user(self, username: str, password: str, role: str = "user") -> UserInDB:
        hashed_password = pwd_context.hash(password)
        user = {
            "username": username,
            "hashed_password": hashed_password,
            "role": role,
        }
        result = await self.users.insert_one(user)
        user["_id"] = str(result.inserted_id)
        return UserInDB(**user)

    async def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        user = await self.get_user(username)
        if user and pwd_context.verify(password, user.hashed_password):
            return user
        return None
