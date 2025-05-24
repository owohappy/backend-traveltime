from fastapi import HTTPException, status
from sqlmodel import Session, select, update, delete
from misc import models, db, logging
from typing import List, Optional
import datetime

def get_all_users(session: Session) -> List[models.User]:
    """Get all users with pagination"""
    try:
        users = session.exec(select(models.User)).all()
        return users
    except Exception as e:
        logging.log(f"Error getting users: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

def get_user_by_id(user_id: int, session: Session) -> models.User:
    """Get user by ID"""
    try:
        user = session.exec(select(models.User).where(models.User.id == user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logging.log(f"Error getting user {user_id}: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )

def update_user(user_id: int, update_data: dict, session: Session) -> models.User:
    """Update user information"""
    try:
        user = get_user_by_id(user_id, session)
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(user, key) and key != "id":
                setattr(user, key, value)
        
        user.updated_at = datetime.datetime.utcnow()
        session.commit()
        session.refresh(user)
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logging.log(f"Error updating user {user_id}: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to update user"
        )

def delete_user(user_id: int, session: Session) -> bool:
    """Delete user"""
    try:
        user = get_user_by_id(user_id, session)
        
        # Delete user
        session.delete(user)
        session.commit()
        
        return True
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logging.log(f"Error deleting user {user_id}: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

def suspend_user(user_id: int, reason: str, session: Session) -> models.User:
    """Suspend a user account"""
    try:
        update_data = {
            "is_active": False,
            "suspension_reason": reason,
            "suspended_at": datetime.datetime.utcnow()
        }
        
        return update_user(user_id, update_data, session)
    except Exception as e:
        logging.log(f"Error suspending user {user_id}: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend user"
        )

def reinstate_user(user_id: int, session: Session) -> models.User:
    """Reinstate a suspended user account"""
    try:
        update_data = {
            "is_active": True,
            "suspension_reason": None,
            "suspended_at": None,
            "reinstated_at": datetime.datetime.utcnow()
        }
        
        return update_user(user_id, update_data, session)
    except Exception as e:
        logging.log(f"Error reinstating user {user_id}: {str(e)}", "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reinstate user"
        )
