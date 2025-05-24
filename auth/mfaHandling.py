from random import random
from datetime import datetime, timedelta
import string
from misc import db


tempTokens = []


def add_mfa_token(userid: str, token: str):
    """
    Adds a new MFA token for the user.
    If the user already has an MFA token, it will be replaced.
    """
    now = datetime.now()
    #create an sql; db
    db.execute("INSERT INTO mfaTokens (userid, mfatoken, created_at) VALUES (?, ?, ?)", (userid, token, now))  # type: ignore
    db.commit()  # type: ignore                                                                                                                                                                                                                                          
    

    return {"valid": True, "reason": "MFA token created"}

def check_mfa(userid: str):
    now = datetime.now()
    result = db.execute("SELECT * FROM mfaTokens WHERE userid = ? AND created_at > ?", (userid, now - timedelta(minutes=5)))  # type: ignore
    return {"valid": bool(result), "reason": "MFA token is valid" if result else "MFA token is invalid"}

def create_mfa_token(userid: str):
    characters = string.ascii_letters + string.digits  # a-zA-Z0-9
    verify = ''.join(random.choices(characters, k=18))   # type: ignore
    add_mfa_token(userid, verify)
    return verify

def check_mfa_token(userid: str, token: str):
    now = datetime.now()
    result = db.execute("SELECT * FROM mfaTokens WHERE userid = ? AND mfatoken = ? AND created_at > ?", (userid, token, now - timedelta(minutes=5)))  # type: ignore
    return {"valid": bool(result), "reason": "MFA token is valid" if result else "MFA token is invalid"}



# Tokens to handle MFA login
def create_temp_token(userid: str):
    characters = string.ascii_letters + string.digits  # a-zA-Z0-9
    verify = ''.join(random.choices(characters, k=18))   # type: ignore
    tempTokens.append({"userid":userid, "temptoken": verify, "exp": datetime.now() + timedelta(seconds=300)})
    return verify

def check_temp_token(userid: str, token: str):
    now = datetime.now()
    for entry in tempTokens:
        if entry["userid"] == userid and entry["temptoken"] == token:
            return {"valid": True}
    return {"valid": False, "reason": "The link can't be found in our database"}