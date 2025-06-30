from fastapi import APIRouter, Request
from auth.accountManagment import is_token_valid
from misc import schemas
from . import travel
from misc import config
from levels.calcXP import calcXP

app = APIRouter(tags=["travel"])
config_data = config.config
debug_mode = config_data['app']['debug']
base_url = config_data['app']['baseURL']
db_name = config_data['app']['nameDB']

@app.post("/heartbeat/{user_id}")
async def heartbeat(user_id: str, ping: schemas.LocationPing, request: Request):
    headers = request.headers
    auth = str(headers.get("Authorization"))
    if is_token_valid(auth):
        try:
            result = travel.gpsinput(user_id, ping.latitude, ping.longitude)
            if result and "duration" in result:
                minutes = result["duration"] / 60 if result["duration"] > 100 else result["duration"]
                calcXP(user_id, minutes)
            return {"success": True, "data": result}
        except Exception as e:
            return {"error": "server error", "detail": str(e)}
    else: 
        return {"error": "Invalid JWT"}
