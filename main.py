# main.py
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from misc import models, schemas
from sqlmodel import SQLModel, Field, Session, create_engine, select
from travel import travel
import time
from misc import email, logging
from fastapi.middleware.cors import CORSMiddleware
from random import randrange
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user, 
    create_verify_token, check_email_token,
    is_token_valid, blacklist_token
)
from sqlalchemy import update

debugBool = True
app = FastAPI()
origins = ["*"]
nameDB = "test"
baseURL= "http://localhost:8000"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if debugBool:
    engine = create_engine("sqlite:///./DB/" + nameDB + "_debug.db")
else:
    engine = create_engine("sqlite:///./DB/" + nameDB + ".db")
SQLModel.metadata.create_all(engine)

# === Database Dependency ===
def get_session():
    with Session(engine) as session:
        yield session

# === Auth Routes ===
@app.post("/register", response_model=schemas.Token)
def register(user: schemas.UserCreate, session: Session = Depends(get_session)):
    if session.exec(select(models.User).where(models.User.email == user.email)).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    userid = randrange(2400000)
    new_user = models.User(id=userid,email=user.email, hashed_password=hash_password(user.password), email_verified=False, name=user.name, phonenumber=user.phonenumber, address=user.address)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    token = create_access_token({"sub": new_user.id})
    verify = create_verify_token(new_user.email)
    if not debugBool:
        email.sendVerfyEmail(new_user.email, verify)
    else: 
        logging.log("Verify URL: http://localhost:8000/user/" + str(new_user.id) + "/verify/" + verify, "debug")
    return {"access_token": token, "token_type": "bearer", "userID": userid}

@app.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, session: Session = Depends(get_session)):
    db_user = session.exec(select(models.User).where(models.User.email == user.email)).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": db_user.id})
    return {"access_token": token, "token_type": "bearer", "userID": db_user.id}

@app.post("/logout")
def logout(token: str = Depends(schemas.Token)):
    blacklist_token(token)
    return {"detail": "Successfully logged out"}

# TODO: add api cooldown for heartbeat
### TODO: (Token based cooldown)

### Account Shit 


@app.get("/user/{user_id}/points")
def user_points(user_id: str, current_user: str = Depends(get_current_user)):
    # Ensure the cfurrent user is accessing their own points
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="You can only access your own points.")
    return {"points": travel.get_user_points(user_id)}

@app.get("/user/{user_id}/getData")
def user_get_data(user_id: str, token: str = Depends(schemas.Token)):
    return None



#TODO: Need to add calls to check/get data for acconuts and pw reset and email verify
@app.post("/user/{db_user.id}/reset_pw/{reset_token}")
def passwdlogic(user_id:str, session: Session = Depends(get_session)):
    return None

@app.post("/user/{email}/resetpw")
def userpasswordreset(email: str, session: Session = Depends(get_session)):
    db_user = session.exec(select(models.User).where(models.User.email == email)).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User with this email does not exist")

    # Create a secure token tied to the email
    reset_token = create_verify_token(email)

    reset_url = f"{baseURL}/user/{db_user.id}/reset_pw/{reset_token}"

    if not debugBool:
       email.sendPasswordResetEmail(db_user.id, reset_token, db_user.email)
    else:
        logging.log(f"Password reset URL for {email}: {reset_url}", "debug")

    return {"status": "success", "message": "If the email exists, a reset link will be sent."}



### Heartbeat for GPS Location:
@app.post("/heartbeat/{user_id}")
async def heartbeat(user_id: str, ping: schemas.LocationPing, request: Request):
    headers = request.headers
    auth = headers.get("Authorization")
    if is_token_valid(auth):
        try:
            travel.gpsinput(user_id, ping.latitude, ping.longitude,)
            return {"succsess": True}
        except:
            return {"error": "server error"}
    else: 
        return {"error":"Invalid JWT"}


### Email Verification stuff
@app.get("/user/{user_id}/verify/{verify}")
def user_verify(user_id: str, verify: str):
    result = check_email_token(user_id, verify)
    if result:
        try:  
            session = Session(engine)
            stmt = update(models.User).where(models.User.name.ilike(f"%{user_id}%")).values(email_verified=True)
            session.execute(stmt)
            session.commit()
            return {"status": "success", "message": "Email verified"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    else:
        return {"status": "error", "message": "Verification failed"}

@app.get("/user/{user_id}/verify/status")
def user_verify_status(user_id: str):
    try:
        # Check if the user exists and retrieve the email_verified status
        user = Session.query(models.User).filter(models.User.user_id == user_id).first()
        if user:
            email_verified = user.email_verified
            return {"status": True, "email_verified": email_verified}
        else:
            return {"status": "error", "message": "User not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

