# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import routes.account
import routes.auth
from misc import logging
import routes.travel
import os


def cls():
    os.system('cls' if os.name=='nt' else 'clear')

cls()

app = FastAPI(version="0.1.0alpha", title="travelpoints API", description="API for travel app", docs_url="/docs", redoc_url="/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Include routes from routes file ===
try:
    app.include_router(routes.auth.app)
    logging.log("Auth routes have been loaded", "info")
except Exception as e:
    logging.log("Error loading auth routes: " + str(e),  "critical")
    pass
try:    
    app.include_router(routes.account.app)
    logging.log("Account routes have been loaded", "info")
except Exception as e:
    logging.log("Error loading account routes: " + str(e), "critical")
    pass
try:
    app.include_router(routes.travel.app)
    logging.log("Travel routes have been loaded", "info")
except Exception as e:
    logging.log("Error loading travel routes: " + str(e), "critical")
    pass

logging.log("API has been started", "success")