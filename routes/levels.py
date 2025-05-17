from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
from misc import db, models
from levels.calcXP import calcXP, getLvl

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
        # Fetch the user from the database
        user = session.exec(select(models.User).where(models.User.userId == userID)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return getLvl(userID)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting level: {str(e)}")