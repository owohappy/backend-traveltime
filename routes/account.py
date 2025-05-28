# main.py
from fastapi import APIRouter, Depends, HTTPException, Header, File, UploadFile
from sqlmodel import Session
from auth.accountManagment import get_current_user
from misc import db, schemas
from . import travel
from misc import logging, config
import account

app = APIRouter(tags=["account"])
jsonConfig = config.config
debugBool = jsonConfig['app']['debug']
nameDB = jsonConfig['app']['nameDB']


@app.get("/user/{user_id}/points")
def user_points(user_id: str, current_user: dict = Depends(get_current_user)):
    '''
    Call to get current points of a UserID with role-based token authentication
    '''
    try:
        # Extract roles from the current_user
        roles = current_user.get("roles", [])
        user_id_from_token = current_user.get("sub")
        
        # Check if user is accessing their own data or has admin role
        if user_id != user_id_from_token and "admin" not in roles:
            raise HTTPException(
                status_code=403, 
                detail="You can only access your own points unless you have admin privileges."
            )
            
        points = travel.get_user_points(user_id) # type: ignore
        return {"points": points, "user_id": user_id}
    except Exception as e:
        if debugBool:
            logging.log("Error getting points: " + str(e), "error")
            raise HTTPException(status_code=500, detail="Error getting points: " + str(e))
        else:
            logging.log("Error getting points: " + str(e), "error")
            raise HTTPException(status_code=500, detail="Error getting points")
    
@app.get("/user/{user_id}/getData")
def user_get_data(user_id: str, token: str = Depends(schemas.Token), session: Session = Depends(db.get_session)):
    '''
    Allowing users to get their data 
    '''
    # get user from DB
    user = account.user_get_data(user_id,session)
    return user

@app.get("/user/{user_id}/getDataHours")
def user_get_data_hours(user_id: str, token: str = Depends(schemas.Token), session: Session = Depends(db.get_session)):
    '''
    Allowing users to get their data 
    '''
    # get user from DB
    user = account.user_get_data_hours(user_id,session)
    return user

@app.post("/user/{user_id}/updateData")
async def user_update_data(user_id: str, field: str = Header(...), data: str = Header(...), token: str = Depends(schemas.Token), file: UploadFile = File(None)):
    '''
    Allowing users to update their info using the field and data headers
    '''
    if not field or not data:
        raise HTTPException(status_code=400, detail="Field and data headers are required.")
    if field not in ["name", "email", "password", "profile_picture"]:
        raise HTTPException(status_code=400, detail="Invalid field specified.")
    # Process the update using the account module
    if not token:
        raise HTTPException(status_code=401, detail="Token is required.")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required.")
    if not data:
        raise HTTPException(status_code=400, detail="Data is required.")
    print(file)
    return await account.user_update_data(user_id,file, field, data ) 
