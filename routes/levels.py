from math import log10
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
from misc import db, models
from levels.calcXP import calcXP

app = APIRouter(tags=["levels"])



@app.get("/xp/{userID}")
def get_xp(userID: int, session: Session = Depends(db.get_session)):
    """
    Get the XP of a user
    """
    try:
        # Fetch the user from the database
        user = session.exec(select(models.User).where(models.User.userId == userID)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"xp": user.xp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting XP: {str(e)}")



@app.get("/level/{userID}")
def get_level(userID: int, session: Session = Depends(db.get_session)):
    """
    Get the level of a user
    """
    try:
        xp = get_xp(userID, session)  # Ensure XP is calculated first
        # do the level log so log(10, xp)
        if xp["xp"] == 0:
            lvl = 0
        else:
            lvl = int(log10(xp["xp"]) / log10(100))  
        return {"level": lvl} 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting level: {str(e)}")