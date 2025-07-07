
from datetime import datetime
from fastapi import HTTPException, status
from sqlmodel import Session, select
from misc import logging, models

# TODO: placeholder user data
users = [
    {"id": 1, "username": "alice", "email": "alice@example.com", "phone": "1234567890", "class": 2},
    {"id": 2, "username": "bob", "email": "bob@example.com", "phone": "0987654321", "class": 1},
]

def delete_user(user_id):
    global users
    user_to_delete = None
    for user in users:
        if user["id"] == user_id and user.get("class") == 2:
            user_to_delete = user
            break
    
    if user_to_delete:
        try:
            users.remove(user_to_delete)
            logging.log(message=f"User {user_id} deleted.", type="info")
            return True
        except HTTPException:
            return None
        except Exception as e:
            logging.log(f"Error deleting user {user_id}: {str(e)}", "error")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )

def suspend_user(user_id, reason, session):
    try:
        user = session.exec(select(models.User).where(models.User.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # TODO: add suspension fields to User model
        logging.log(f"User {user_id} suspended: {reason}", "info")
        return user
        
    except Exception as e:
        logging.log(f"Suspend error: {e}", "error")
        raise HTTPException(status_code=500, detail="Suspend failed")


def reinstate_user(user_id, session):
    try:
        user = session.exec(select(models.User).where(models.User.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # TODO: add reinstatement logic
        logging.log(f"User {user_id} reinstated", "info")
        return user
        
    except Exception as e:
        logging.log(f"Reinstate error: {e}", "error")
        raise HTTPException(status_code=500, detail="Reinstate failed")

