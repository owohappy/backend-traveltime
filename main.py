# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import routes.account
import routes.auth
import routes.misc
import routes.travel
import routes.gamling
import routes.levels
import routes.admin
from misc import logging, db
import misc.models
import os
import logging as log
import ssl

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
)
log.getLogger('passlib').setLevel(log.ERROR)

# Load DB and routes
try: 
    db.init_database()
    logging.log("DB loaded", "info")

except Exception as e:
    logging.log(f"DB error: {e}", "critical")

routes_to_load = [
    (routes.auth.app, "auth"),
    (routes.account.app, "account"),
    (routes.travel.app, "travel"),
    (routes.misc.app, "misc"),
    (routes.gamling.app, "gambling"),
    (routes.levels.app, "levels"),
    (routes.admin.app, "admin"),
]

for router, name in routes_to_load:
    try:
        app.include_router(router)
        logging.log(f"{name} routes loaded", "info")
    except Exception as e:
        logging.log(f"{name} routes failed: {e}", "critical")

logging.log("API started", "success")