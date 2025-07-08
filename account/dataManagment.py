from misc import models, logging
from sqlmodel import Session, select
from fastapi import HTTPException, status, File, UploadFile
from misc import db, schemas

def get_user_data(user_id: str, session: Session):
    user = session.exec(select(models.User).where(models.User.id == int(user_id))).first()
    if not user:
        logging.log(f"User {user_id} not found", "warning")
        raise HTTPException(status_code=404, detail="User not found")
    
    points = user.points if user.points else 0

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
    user = session.exec(select(models.User).where(models.User.id == int(user_id))).first()
    if not user:
        logging.log(f"User {user_id} not found", "warning")
        raise HTTPException(status_code=404, detail="User not found")
    
    allowed_fields = {"name", "phonenumber", "address"}
    if field not in allowed_fields and file is None:
        raise HTTPException(status_code=400, detail="Field not allowed")
    
    if file:
        # simple file upload for profile pics
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
    user_hours = session.exec(select(models.UserHours).where(models.UserHours.user_id == int(user_id))).first()
    if not user_hours:
        # Create UserHours record if it doesn't exist
        user_hours = models.UserHours(user_id=int(user_id))
        session.add(user_hours)
        session.commit()
        session.refresh(user_hours)
        logging.log(f"Created UserHours record for user {user_id}", "info")
    
    # struct for hours data
    return {
        "id": user_hours.id,
        "user_id": user_hours.user_id,
        "hours": {
            "total": user_hours.hoursTotal,
            "weekly": user_hours.hoursWeekly,
            "monthly": user_hours.hoursMonthly,
            "daily": user_hours.hoursDaily    
        },
        "transport": {
            "bus": {
                "total": user_hours.bus_hoursTotal,
                "weekly": user_hours.bus_hoursWeekly,
                "monthly": user_hours.bus_hoursMonthly,
                "daily": user_hours.bus_hoursDaily    
            },
            "train": {
                "total": user_hours.train_hoursTotal,
                "weekly": user_hours.train_hoursWeekly,
                "monthly": user_hours.train_hoursMonthly,
                "daily": user_hours.train_hoursDaily    
            },
            "ferry": {  # was "fairy" lol
                "total": user_hours.ferry_hoursTotal,
                "weekly": user_hours.ferry_hoursWeekly,
                "monthly": user_hours.ferry_hoursMonthly,
                "daily": user_hours.ferry_hoursDaily    
            },
        }
    }