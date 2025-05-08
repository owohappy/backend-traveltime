# main.py
from fastapi import APIRouter, Depends, HTTPException, Header
from auth.accountManagment import get_current_user
from misc import schemas
from travel import travel
from misc import logging, config
import account

app = APIRouter(tags=["account"])
jsonConfig = config.config
debugBool = jsonConfig['app']['debug']
nameDB = jsonConfig['app']['nameDB']


@app.get("/user/{user_id}/points")
def user_points(user_id: str, current_user: str = Depends(get_current_user)):
    '''
    Call to get current points of a UserID (TODO: rolebased tokens) (currently locked to userID of JWT)
    '''
    # Ensure the cfurrent user is accessing their own points
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="You can only access your own points.")
    try:
        points = travel.get_user_points(user_id)
        return {"points": points}
    except Exception as e:
        if debugBool:
            logging.log("Error getting points: " + str(e), "error")
            raise HTTPException(status_code=500, detail="Error getting points: " + str(e))
        else:
            logging.log("Error getting points: " + str(e), "error")
            raise HTTPException(status_code=500, detail="Error getting points")
    
@app.get("/user/{user_id}/getData")
def user_get_data(user_id: str, token: str = Depends(schemas.Token)):
    '''
    Allowing users to get their data 
    '''
    #TODO: Auth
    return None

@app.post("/user/{user_id}/updateData")
async def user_update_data(user_id: str, field: str = Header(...), data: str = Header(...), token: str = Depends(schemas.Token)):
    '''
    Allowing users to update their info using the field and data headers
    '''
    #TODO: Auth
    return await account.process_headers(user_id, field, data, token)
