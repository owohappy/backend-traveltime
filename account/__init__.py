from fastapi import Depends, Header
from misc import schemas

def user_get_data(user_id: str, token: str = Depends(schemas.Token)):
    '''
    Allowing users to get their data 
    '''
    return None

async def user_update_data(user_id: str, field: str = Header(...), data: str = Header(...), token: str = Depends(schemas.Token)):
    '''
    Allowing users to update their info using the field and data headers
    '''
    return None