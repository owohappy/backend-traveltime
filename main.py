# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import routes
import routes.auth

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



