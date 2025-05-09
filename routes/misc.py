from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
from misc import db, models

app = APIRouter(tags=["misc"])

@app.get("/stats/users_count")
def get_users_count(session: Session = Depends(db.get_session)):
    """
    Returns the total number of registered users.
    """
    count = session.exec(select(models.User)).count()
    return {"users_count": count}

@app.get("/stats/points_total")
def get_points_total(session: Session = Depends(db.get_session)):
    """
    Returns the total amount of points earned by all users.
    """     
    total = session.exec(select(models.UserPoints)).all()
    points_sum = sum(up.points for up in total)
    return {"points_total": points_sum}

@app.get("/stats/leaderboard")
def get_leaderboard(session: Session = Depends(db.get_session)):
    """
    Returns a leaderboard of the top 10 members by points.
    """
    statement = select(models.UserPoints).order_by(desc(models.UserPoints.points)).limit(10)
    top_points = session.exec(statement).all()
    leaderboard = []
    for entry in top_points:
        user = session.exec(select(models.User).where(models.User.id == entry.user_id)).first()
        leaderboard.append({
            "user_id": entry.user_id,
            "email": user.email if user else None,
            "points": entry.points
        })
    return leaderboard

@app.get("/ping")
def ping():
    """
    Returns a simple 'pong' response to check if the server is running.
    """
    return {"message": "pong"}

