from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
from typing import Optional
from misc import db, models, logging
from sqlalchemy import func

app = APIRouter(tags=["misc"])

@app.get("/stats/users_count")
def get_users_count(session: Session = Depends(db.get_session)):
    """
    Returns the total number of registered users.
    """
    try:
        count = session.exec(select(models.User)).count() # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting users")
    if count is None:
        raise HTTPException(status_code=404, detail="No users found")
    return {"users_count": count}

@app.get("/stats/leaderboard")
def get_leaderboard(types: Optional[str] = None, session: Session = Depends(db.get_session)):
    """
    Returns the leaderboard sorted by XP in descending order.
    Types: total, daily, weekly, monthly
    """
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
            raise HTTPException(status_code=400, detail="Invalid type parameter")
    except Exception as e:
        logging.log("Error fetching leaderboard: " + str(e), "error")
        raise HTTPException(status_code=500, detail="Error fetching leaderboard")
    
    if not leaderboard:
        raise HTTPException(status_code=404, detail="No users found")
    
    return {"leaderboard": [user.dict() for user in leaderboard]}

@app.get("/ping")
def ping():
    """
    Returns a simple 'pong' response to check if the server is running.
    """
    return {"message": "pong"}

@app.get("/stats/points_total")
def get_total_points(session: Session = Depends(db.get_session)):
    """
    Returns the total points earned by all users.
    """
    try:
        # Use SQLAlchemy's func.sum to calculate total points
        result = session.query(func.sum(models.User.points)).scalar()
        total = result or 0
        return {"points_total": total}
    except Exception as e:
        logging.log(f"Error calculating total points: {str(e)}", "error")
        raise HTTPException(status_code=500, detail="Error calculating total points")

