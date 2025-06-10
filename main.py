# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from misc import logging, db
import os
import logging as log
import misc.config as config


def cls():
    os.system('cls' if os.name=='nt' else 'clear')

cls()

app = FastAPI(version="0.0.3", title="travelpoints API", description="API for travelpoints app", docs_url="/docs", redoc_url="/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)ut
log.getLogger('passlib').setLevel(log.ERROR)

config.load_config()
# === Include routes from routes file ===

from routes.account import app as account_app
import routes.auth
import routes.misc
import routes.travel

try: 
    db.init_database()
    logging.log("Database have been loaded", "info")
except Exception as e:
    logging.log("Error loading database: " + str(e), "critical")
    pass
try:
    app.include_router(routes.auth.app)
    logging.log("Auth routes have been loaded", "info")
except Exception as e:
    logging.log("Error loading auth routes: " + str(e),  "critical")
    pass
try:    
    app.include_router(account_app)
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

try:
    app.include_router(routes.misc.app)
    logging.log("Travel routes have been loaded", "info")
except Exception as e:
    logging.log("Error loading travel routes: " + str(e), "critical")
    pass

logging.log("API has been started", "success")