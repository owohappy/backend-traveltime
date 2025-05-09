# main.py
from fastapi import APIRouter, Request
from auth.accountManagment import is_token_valid
from misc import schemas
from travel import travel
from misc import config

app = APIRouter(tags=["travel"])
jsonConfig = config.config
debugBool = jsonConfig['app']['debug']
baseURL = jsonConfig['app']['baseURL']
nameDB = jsonConfig['app']['nameDB']

### Heartbeat for GPS Location:
@app.post("/heartbeat/{user_id}")
async def heartbeat(user_id: str, ping: schemas.LocationPing, request: Request):
    '''
    Using GPS loc in a cords. format we get the users position and try to estimate the current route a user is on
    '''
    #get headers with auth token
    headers = request.headers
    auth = headers.get("Authorization")
    if is_token_valid(auth):
        try:
            print(travel.gpsinput(user_id, ping.latitude, ping.longitude,))
            return {"succsess": True}
        except:
            return {"error": "server error"}
    else: 
        return {"error":"Invalid JWT"}
    
@app.post("/user/{user_id}/confirm_travel/{travel_id}")
def confirm_travel(user_id: str, travel_id: str, request: Request):
    '''
    Used to confirm the travle with some form of proof(TODO)
    '''
    #get headers with auth token
    headers = request.headers
    auth = headers.get("Authorization")
    if is_token_valid(auth):
        try:
            travel.confirm_travel(user_id, travel_id)
            return {"success": True}
        except:
            return {"error": "server error"}
    else: 
        return {"error":"Invalid JWT"}    


