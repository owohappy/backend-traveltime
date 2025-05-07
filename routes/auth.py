from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from random import randrange
import logging
from misc import config, schemas, models
from auth import hash_password, is_token_valid, verify_password, create_access_token, create_verify_token, blacklist_token
from misc import email
from sqlmodel import SQLModel, Field, Session, create_engine, select

app = APIRouter()
jsonConfig = config.config
debugBool = jsonConfig['app']['debug']
baseURL = jsonConfig['app']['baseURL']
nameDB = jsonConfig['app']['nameDB']

# Setup DB
if debugBool:
    try:
        engine = create_engine("sqlite:///./db/" + nameDB + "_debug.db")
        SQLModel.metadata.create_all(engine)
    except Exception as e:
            logging.log("Error creating engine: " + str(e), "critical")
else:
    try:
        engine = create_engine("sqlite:///./db/" + nameDB + ".db")
        SQLModel.metadata.create_all(engine)
    except Exception as e:
            logging.log("Error creating engine: " + str(e), "critical")

def get_session():
    with Session(engine) as session:
        yield session


# === Auth Routes ===


@app.post("/register", response_model=schemas.Token)
def register(user: schemas.UserCreate, session: Session = Depends(get_session)):
    '''
    Register a user and return a token
    '''
    # Check if the email already exists in the database
    if session.exec(select(models.User).where(models.User.email == user.email)).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Generate a unique user ID
    userid = randrange(100000, 999999)
    while session.exec(select(models.User).where(models.User.id == userid)).first():
        userid = randrange(100000, 999999)

    new_user = models.User(
        id=userid,
        email=user.email,
        hashed_password=hash_password(user.password),
        email_verified=False,
        name=user.name,
        phonenumber=user.phonenumber,
        address=user.address,
    )

    try:
        with session.begin():
            session.add(new_user)
            token = create_access_token({"sub": new_user.id})
            verify = create_verify_token(new_user.email)

        if not debugBool:
            email.sendVerfyEmail(new_user.email, verify)
        else:
            logging.log("Verify URL: " + baseURL + "/user/" + str(new_user.id) + "/verify/" + verify, "debug")

    except Exception as e:
        logging.log("Registration failed: " + str(e), "error")
        raise HTTPException(status_code=500, detail="Registration failed")

    return {"access_token": token, "token_type": "bearer", "userID": userid}




@app.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, session: Session = Depends(get_session)):
    '''
    login a user and return a token'''
    # Check if the user exists in the database
    db_user = session.exec(select(models.User).where(models.User.email == user.email)).first()
    # If the user does not exist or the password is incorrect, raise an error
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    # If the user is not verified, raise an error
    # try to create a token
    try:
        token = create_access_token({"sub": db_user.id})
        return {"access_token": token, "token_type": "bearer", "userID": db_user.id}
    except Exception as e:
        # Handle the error and return a response
        if debugBool:
            logging.log("Error creating token: " + str(e), "error")
            raise HTTPException(status_code=500, detail="Error creating token: " + str(e))
        else:
            logging.log("Error creating token: " + str(e), "error")
            raise HTTPException(status_code=500, detail="Error creating token")
        


@app.post("/logout")
def logout(token: str = Depends(schemas.Token)):
    '''
    logout a user by blacklisting the token
    '''
    try:
        # Check if the token is valid
        if not is_token_valid(token):
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        # Handle the error and return a response
        if debugBool:
            logging.log("Error checking token: " + str(e), "error")
            raise HTTPException(status_code=500, detail="Error checking token: " + str(e))
        else:
            logging.log("Error checking token: " + str(e), "error")
            raise HTTPException(status_code=500, detail="Error checking token")
    try:
        # Blacklist the token
        blacklist_token(token)
    except Exception as e:
        # Handle the error and return a response
        if debugBool:
            logging.log("Error blacklisting token: " + str(e), "error")
            raise HTTPException(status_code=500, detail="Error blacklisting token: " + str(e))
        else:
            logging.log("Error blacklisting token: " + str(e), "error")
            raise HTTPException(status_code=500, detail="Error blacklisting token")
    # Return a success message
    if not debugBool:
        return {"status": "success", "message": "User logged out"}
    else:
        logging.log("User logged out", "debug")
        return {"status": "success", "message": "User logged out"}



@app.post("/user/{db_user.id}/reset_pw/{reset_token}")
def passwdlogic(user_id:str, session: Session = Depends(get_session)):
    return None

@app.post("/user/{email}/resetpw")
def userpasswordreset(email: str, session: Session = Depends(get_session)):
    '''
    Send a password reset email to the user with the given email address.
    '''
    # Check if the email exists in the database
    db_user = session.query(models.User).filter(models.User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User with this email does not exist")

    # Create a secure token tied to the email
    try:
        # Create a token for the user
        reset_token = create_verify_token(email)
    except Exception as e:
        # Handle the error and return a response
        if debugBool:
            raise HTTPException(status_code=500, detail="Error creating token: " + str(e))
        else:
            raise HTTPException(status_code=500, detail="Error creating token")

    # Create the password reset URL
    reset_url = f"{baseURL}/user/{db_user.id}/reset_pw/{reset_token}"

    # Send the password reset email
    # Use the email module to send the email
    # If debug mode is enabled, log the URL instead of sending the email
    if not debugBool:
       email.sendPasswordResetEmail(db_user.id, reset_token, db_user.email)
    else:
        logging.log(f"Password reset URL for {email}: {reset_url}", "debug")

    return {"status": "success", "message": "If the email exists, a reset link will be sent."}