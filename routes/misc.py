from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
from typing import Optional
from misc import db, models, logging
from sqlalchemy import func

app = APIRouter(tags=["misc"])

@app.get("/stats/users_count")
def get_users_count(session: Session = Depends(db.get_session)):
    try:
        count = session.exec(select(models.User)).count()
        return {"users_count": count}
    except Exception:
        raise HTTPException(status_code=500, detail="Error counting users")

@app.get("/stats/leaderboard")
def get_leaderboard(types: Optional[str] = None, session: Session = Depends(db.get_session)):
    try:
        if types == "total" or types is None:
            leaderboard = session.exec(select(models.UserHours).order_by(desc(models.UserHours.hoursTotal))).all()
        elif types == "daily":
            leaderboard = session.exec(select(models.UserHours).order_by(desc(models.UserHours.hoursDaily))).all()
        elif types == "weekly":
            leaderboard = session.exec(select(models.UserHours).order_by(desc(models.UserHours.hoursWeekly))).all()
        elif types == "monthly":
            leaderboard = session.exec(select(models.UserHours).order_by(desc(models.UserHours.hoursMonthly))).all()
        else:
            raise HTTPException(status_code=400, detail="Invalid type")
    except Exception as e:
        logging.log("Error fetching leaderboard: " + str(e), "error")
        raise HTTPException(status_code=500, detail="Database error")
    
    if not leaderboard:
        return {"leaderboard": []}
    
    return {"leaderboard": [user.dict() for user in leaderboard]}

@app.get("/ping")
def ping():
    return {"message": "pong"}

@app.get("/stats/points_total")
def get_total_points(session: Session = Depends(db.get_session)):
    try:
        result = session.query(func.sum(models.User.points)).scalar()
        total = result or 0
        return {"points_total": total}
    except Exception as e:
        logging.log(f"Error calculating total points: {str(e)}", "error")
        raise HTTPException(status_code=500, detail="Database error")

