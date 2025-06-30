from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from auth.accountManagment import get_current_user
from misc import logging, db
import admin.handleUsers as admin_handler

app = APIRouter(tags=["admin"], prefix="/admin")

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    roles = current_user.get("roles", [])
    if "admin" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    try:
        result = admin_handler.delete_user(user_id)
        return result
    except Exception as e:
        logging.log(f"Delete user error: {e}", "error")
        raise HTTPException(status_code=500, detail="Delete failed")

@app.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    reason: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    roles = current_user.get("roles", [])
    if "admin" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    
    try:
        result = admin_handler.suspend_user(user_id, reason, session)
        return {"message": "User suspended", "user": result}
    except Exception as e:
        logging.log(f"Suspend error: {e}", "error")
        raise HTTPException(status_code=500, detail="Suspend failed")

@app.post("/users/{user_id}/reinstate")
async def reinstate_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    roles = current_user.get("roles", [])
    if "admin" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    
    try:
        result = admin_handler.reinstate_user(user_id, session)
        return {"message": "User reinstated", "user": result}
    except Exception as e:
        logging.log(f"Reinstate error: {e}", "error")
        raise HTTPException(status_code=500, detail="Reinstate failed")