from random import random
from datetime import datetime, timedelta
import string

mfaTokens = []
tempTokens = []



def create_mfa_token(userid: str):
    characters = string.ascii_letters + string.digits  # a-zA-Z0-9
    verify = ''.join(random.choices(characters, k=18))  
    mfaTokens.append({"userid":userid, "mfatoken": verify})
    return verify

def check_mfa_token(userid: str, token: str):
    now = datetime.now()
    for entry in mfaTokens:
        if entry["userid"] == userid and entry["mfatoken"] == token:
            return {"valid": True}
    return {"valid": False, "reason": "The link can't be found in our database"}



# Tokens to handle MFA login
def create_temp_token(userid: str):
    characters = string.ascii_letters + string.digits  # a-zA-Z0-9
    verify = ''.join(random.choices(characters, k=18))  
    tempTokens.append({"userid":userid, "temptoken": verify, "exp": datetime.now() + timedelta(seconds=300)})
    return verify

def check_temp_token(userid: str, token: str):
    now = datetime.now()
    for entry in tempTokens:
        if entry["userid"] == userid and entry["temptoken"] == token:
            return {"valid": True}
    return {"valid": False, "reason": "The link can't be found in our database"}