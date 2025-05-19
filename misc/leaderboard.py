from sqlmodel import select, desc, Session
from misc import db, models, logging
from typing import Optional, List

def get_leaderboard(limit: int = 10, type: str = "total") -> List[dict]:
    """
    Get the leaderboard for a given type
    """
    try:
        with Session(db.engine) as session:
            if type == "total" or type is None:
                users = session.exec(select(models.User).order_by(desc(models.User.points)).limit(limit)).all()
            elif type == "xp":
                users = session.exec(select(models.User).order_by(desc(models.User.xp)).limit(limit)).all()
            else:
                return []
                
            return [
                {
                    "id": user.id,
                    "name": user.name or "Anonymous",
                    "points": user.points,
                    "xp": user.xp,
                    "level": user.level
                }
                for user in users
            ]
    except Exception as e:
        logging.log(f"Error getting leaderboard: {str(e)}", "error")
        return []