from math import log10
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from misc import db, models
from levels.calcXP import calcXP

app = APIRouter(tags=["levels"])

@app.get("/xp/{userID}")
def get_xp(userID: int, session: Session = Depends(db.get_session)):
    try:
        user = session.exec(select(models.User).where(models.User.id == userID)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"xp": user.xp}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/level/{userID}")
def get_level(userID: int, session: Session = Depends(db.get_session)):
    try:
        xp_data = get_xp(userID, session)
        if xp_data["xp"] == 0:
            level = 0
        else:
            level = int(log10(xp_data["xp"]) / log10(100))  
        return {"level": level} 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")