from datetime import datetime
from cairo import Status
from fastapi import HTTPException
from sqlmodel import Session
from misc import logging, models

#TODO: WHOLE FILE IS A TODO
# Assuming a simple in-memory user store for demonstration
users = [
    {"id": 1, "username": "alice", "email": "alice@example.com", "phone": "1234567890", "class": 2},
    {"id": 2, "username": "bob", "email": "bob@example.com", "phone": "0987654321", "class": 1},
    # Add more users as needed
]

def deleteUser(user_id):
    """
    Deletes a user from the system if their class is 2.
    """
    global users
    user_to_delete = None
    for user_in_list in users:
        if user_in_list["id"] == user_id and user_in_list.get("class") == 2:
            user_to_delete = user_in_list
            break  # Found the user, no need to continue iterating
    
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
                status_code=Status.HTTP_500_INTERNAL_SERVER_ERROR, # type: ignore
                detail="Failed to delete user"
            )

def suspend_user(user_id: int, reason: str, session: Session) -> models.User:
    """Suspend a user account"""
    try:
        update_data = {
            "is_active": False,
            "suspension_reason": reason,
            "suspended_at": datetime.utcnow()
        }
        
        return update_user(user_id, update_data, session) # type: ignore
    except Exception as e:
        logging.log(f"Error suspending user {user_id}: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # type: ignore
            detail="Failed to suspend user"
        )

def reinstate_user(user_id: int, session: Session) -> models.User:
    """Reinstate a suspended user account"""
    try:
        update_data = {
            "is_active": True,
            "suspension_reason": None,
            "suspended_at": None,
            "reinstated_at": datetime.utcnow()
        }
        
        return update_user(user_id, update_data, session) # type: ignore
    except Exception as e:
        logging.log(f"Error reinstating user {user_id}: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # type: ignore
            detail="Failed to reinstate user"
        )
