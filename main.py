# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from misc import models, schemas
from sqlmodel import SQLModel, Field, Session, create_engine, select
from travel import travel
import time 
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user
)

app = FastAPI()
engine = create_engine("sqlite:///./DB/test.db")
SQLModel.metadata.create_all(engine)

# === Database Dependency ===
def get_session():
    with Session(engine) as session:
        yield session

# === Auth Routes ===
@app.post("/register", response_model=schemas.Token)
def register(user: schemas.UserCreate, session: Session = Depends(get_session)):
    if session.exec(select(User).where(User.email == user.email)).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(email=user.email, hashed_password=hash_password(user.password))
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    token = create_access_token({"sub": new_user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.email == user.email)).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

# === Protected Route Example ===
@app.get("/me")
def read_current_user(email: str = Depends(get_current_user)):
    return {"email": email}


@app.post("/heartbeat")
async def heartbeat(ping: LocationPing):
    return await travel.check_if_on_transit(
        ping.user_id,
        ping.latitude,
        ping.longitude,
        ping.timestamp
    )

@app.get("/user/{user_id}/log")
def user_log(user_id: str):
    return travel.get_user_log(user_id)

@app.get("/user/{user_id}/points")
def user_points(user_id: str, current_user: str = Depends(get_current_user)):
    # Ensure the current user is accessing their own points
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="You can only access your own points.")
    return {"points": travel.get_user_points(user_id)}
