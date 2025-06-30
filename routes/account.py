from fastapi import APIRouter, Depends, Form, HTTPException, Header, File, Query, UploadFile
from fastapi.responses import FileResponse
import shutil
from sqlmodel import Session
from auth.accountManagment import get_current_user
from misc import db, schemas
from . import travel
from misc import logging, config
import auth
import account

app = APIRouter(tags=["account"])
config_data = config.config
debug_mode = config_data['app']['debug']
db_name = config_data['app']['nameDB']


@app.get("/user/{user_id}/points")
def user_points(user_id: str, current_user: dict = Depends(get_current_user)):
    try:
        roles = current_user.get("roles", [])
        user_id_from_token = current_user.get("sub")
        
        if user_id != user_id_from_token and "admin" not in roles:
            raise HTTPException(
                status_code=403, 
                detail="You can only access your own points unless you have admin privileges."
            )
            
        points = travel.get_user_points(user_id)
        return {"points": points, "user_id": user_id}
    except Exception as e:
        if debug_mode:
            logging.log("Error getting points: " + str(e), "error")
            raise HTTPException(status_code=500, detail="Error getting points: " + str(e))
        else:
            logging.log("Error getting points: " + str(e), "error")
            raise HTTPException(status_code=500, detail="Error getting points")
    
@app.get("/user/{user_id}/getData")
def user_get_data(user_id: str, token: str = Depends(schemas.Token), session: Session = Depends(db.get_session)):
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
async def user_update_data(
    user_id: str, 
    file: UploadFile = File(...),
    access_token: str = Query(None)
):
    field = "name"
    data = "Lucas Roeder"
    contents = await file.read()
    # Using access_token from query parameters instead of token dependency
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token is required.")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required.")
    
    return await account.user_update_data(user_id, contents, field, data)

@app.post("/user/{user_id}/updatePicture")
async def create_upload_file(user_id: str, file: UploadFile, access_token: str = Query(...),):
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token is required.")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required.")
    # Save the file to a specific location
    file_location = f"misc/templates/pfp/{user_id}.jpg"
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())    

    print(f"File received: {file.filename}")
    return {"filename"}
@app.get("/misc/templates/pfp/{user_id}.jpg")
def get_user_picture(user_id: str):
    """
    Endpoint to retrieve user profile picture.
    """
    file_location = f"misc/templates/pfp/{user_id}.jpg"
    try:
        return FileResponse(file_location, media_type="image/jpeg")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Profile picture not found.")
    except Exception as e:
        logging.log(f"Error retrieving profile picture for user {user_id}: {str(e)}", "error")
        raise HTTPException(status_code=500, detail="Error retrieving profile picture.")
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
    return account.process_headers(user_id, field, data, token) # type: ignore
    if file != File(None):
        # If a file is provided, process it
        with open(f"uploads/{user_id +".jpg"}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
    return None
