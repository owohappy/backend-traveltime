# main.py
from fastapi import FastAPI
from misc import config
from fastapi.middleware.cors import CORSMiddleware
from random import randrange
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user, 
    create_verify_token, check_email_token,
    is_token_valid, blacklist_token
)
from sqlalchemy import update
import routes
import routes.auth

# get data from json file and set config
jsonConfig = config.config
debugBool = jsonConfig['app']['debug']

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# === Include routes from routes file ===
app.include_router(routes.auth.app)



