from misc import models, logging
from sqlmodel import Session, select
from fastapi import HTTPException, status, File, UploadFile
from misc import db, schemas
def get_user_data(user_id: str, session: Session):
    points: int = 0
    user = session.exec(select(models.User).where(models.User.id == int(user_id))).first()
    if not user:
        logging.log(f"User {user_id} not found", "warning")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user.points is not None:
        points = user.points


    
    # Return user data except sensitive fields
    return {
        "id": user.id,
        "email": user.email,
        "email_verified": user.email_verified,
        "name": user.name,
        "phonenumber": user.phonenumber,
        "address": user.address,
        "created_at": user.created_at,
        "email_verified_at": user.email_verified_at,
        "mfa": user.mfa,
        "pfp_url": user.pfp_url,
        "points": points,
        
    }

def update_user_data(user_id: str, field: str, data: str, file, session: Session):
    session = db.get_session()
    user = session.exec(select(models.User).where(models.User.id == int(user_id))).first()
    if not user:
        logging.log(f"User {user_id} not found", "warning")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Only allow updating certain fields
    allowed_fields = {"name", "phonenumber", "address"}
    if (field not in allowed_fields and file == None):
        raise HTTPException(status_code=400, detail="Field not allowed to be updated")
    if file != None:
        file_location = f"misc/templates/pfp/{user_id}.jpg"
        with open(file_location, "wb") as buffer:
            buffer.write(file)
        setattr(user, "pfp_url", file_location)
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"success": True, "updated_field": "pfp_url", "new_value": file_location}
    setattr(user, field, data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"success": True, "updated_field": field, "new_value": data}

def get_user_data_hours(user_id: str, session: Session):
    user_hours = session.exec(select(models.UserHours).where(models.UserHours.user_id == int(user_id))).first() # type: ignore
    if not user_hours:
        logging.log(f"User {user_id} not found", "warning")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return {
        "id": user_hours.id,
        "user_id": user_hours.user_id,
        "hours": {
            "hoursTotal": user_hours.hoursTotal,
            "hoursWeekly": user_hours.hoursWeekly,
            "hoursMonthly": user_hours.hoursMonthly,
            "hoursDaily": user_hours.hoursDaily    
        },
        "transport": {
            "bus": {
                "hoursTotal": user_hours.hoursTotal,
                "hoursWeekly": user_hours.hoursWeekly,
                "hoursMonthly": user_hours.hoursMonthly,
                "hoursDaily": user_hours.hoursDaily    
            },
            "train": {
                "hoursTotal": user_hours.hoursTotal,
                "hoursWeekly": user_hours.hoursWeekly,
                "hoursMonthly": user_hours.hoursMonthly,
                "hoursDaily": user_hours.hoursDaily    
            },
            "fairy": {
                "hoursTotal": user_hours.hoursTotal,
                "hoursWeekly": user_hours.hoursWeekly,
                "hoursMonthly": user_hours.hoursMonthly,
                "hoursDaily": user_hours.hoursDaily    
            },
        }
    }