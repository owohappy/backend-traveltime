from fastapi import Depends, Header, HTTPException, File, UploadFile
from misc import schemas, db
from . import dataManagment

def user_get_data(user_id: str, session=Depends(db.get_session)):
    '''
    Allowing users to get their data 
    '''
    return dataManagment.get_user_data(user_id, session)

async def user_update_data(
    user_id: str,
    field: str = Header(...),
    data: str = Header(...),
    file: UploadFile = File(None),
    session=db.get_session
):
    '''
    Allowing users to update their info using the field and data headers
    '''
    return dataManagment.update_user_data(user_id, field, data, file, session)

async def user_get_data_hours(
    user_id: str,
    session=Depends(db.get_session)
):
    '''
    Allowing users to get their data 
    '''
    return dataManagment.get_user_data_hours(user_id, session)