from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
from misc import db, models

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

@app.get("/stats/points_total")
def get_points_total(session: Session = Depends(db.get_session)):
    """
    Returns the total amount of points earned by all users.
    """
    try:
        total = session.exec(select(models.UserPoints)).all()
        points_sum = sum(up.points for up in total)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating total points")
    if points_sum is None:
        raise HTTPException(status_code=404, detail="No points found")
    return {"points_total": points_sum}

@app.get("/stats/leaderboard")
def get_leaderboard(session: Session = Depends(db.get_session)):
    """
    Returns a leaderboard of the top 10 members by points.
    """
    statement = select(models.UserPoints).order_by(desc(models.UserPoints.points)).limit(10)
    top_points = session.exec(statement).all()
    leaderboard = []
    # Check if there are any users with points already exsisting
    if not top_points:
        raise HTTPException(status_code=404, detail="No points found")
    
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

