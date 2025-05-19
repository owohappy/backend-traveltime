# main.py
from fastapi import APIRouter, Request
from auth.accountManagment import is_token_valid
from misc import schemas
from travel import travel
from misc import config
from levels.calcXP import calcXP

app = APIRouter(tags=["travel"])
jsonConfig = config.config
debugBool = jsonConfig['app']['debug']
baseURL = jsonConfig['app']['baseURL']
nameDB = jsonConfig['app']['nameDB']

### Heartbeat for GPS Location:
@app.post("/heartbeat/{user_id}")
async def heartbeat(user_id: str, ping: schemas.LocationPing, request: Request):
    '''
    Using GPS loc in a cords. format we get the users position and try to estimate the current route a user is on.
    The output of travel.gpsinput is used to count the hours.
    '''
    headers = request.headers
    auth: str = str(headers.get("Authorization"))
    if is_token_valid(auth):
        try:
            result = travel.gpsinput(user_id, ping.latitude, ping.longitude)
            # Assume result contains duration in seconds or minutes
            # You may need to adjust this depending on gpsinput's return value
            if result and "duration" in result:
                # duration should be in minutes for calcXP
                minutes = result["duration"] / 60 if result["duration"] > 100 else result["duration"]
                calcXP(user_id, minutes)
            return {"success": True, "data": result}
        except Exception as e:
            return {"error": "server error", "detail": str(e)}
    else: 
        return {"error": "Invalid JWT"}
