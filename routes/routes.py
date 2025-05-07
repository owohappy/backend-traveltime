# main.py
from fastapi import APIRouter, Depends, HTTPException, Request
from misc import models, schemas
from sqlmodel import SQLModel, Field, Session, create_engine, select
from travel import travel
from misc import email, logging, config
from fastapi.middleware.cors import CORSMiddleware
from random import randrange
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user, 
    create_verify_token, check_email_token,
    is_token_valid, blacklist_token
)
from sqlalchemy import update


app = APIRouter()
jsonConfig = config.config
debugBool = jsonConfig['app']['debug']
baseURL = jsonConfig['app']['baseURL']
nameDB = jsonConfig['app']['nameDB']

# Setup DB
if debugBool:
    engine = create_engine("sqlite:///./db/" + nameDB + "_debug.db")
else:
    engine = create_engine("sqlite:///./db/" + nameDB + ".db")
SQLModel.metadata.create_all(engine)

# === Middleware ===
def get_session():
    with Session(engine) as session:
        yield session


# TODO: add api cooldown for heartbeat
### TODO: (Token based cooldown)


# User data handling for points and general data 

@app.get("/user/{user_id}/points")
def user_points(user_id: str, current_user: str = Depends(get_current_user)):
    # Ensure the cfurrent user is accessing their own points
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="You can only access your own points.")
    try:
        points = travel.get_user_points(user_id)
        return {"points": points}
    except Exception as e:
        if debugBool:
            logging.log("Error getting points: " + str(e), "error")
            raise HTTPException(status_code=500, detail="Error getting points: " + str(e))
        else:
            logging.log("Error getting points: " + str(e), "error")
            raise HTTPException(status_code=500, detail="Error getting points")
    

@app.get("/user/{user_id}/getData")
def user_get_data(user_id: str, token: str = Depends(schemas.Token)):
    return None



#TODO: Need to add calls to check/get data for acconuts and pw reset and email verify




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
