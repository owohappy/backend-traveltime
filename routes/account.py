from fastapi import APIRouter, Depends, Form, HTTPException, Header, File, Query, UploadFile, status
from fastapi.responses import FileResponse
import shutil
import os
from datetime import datetime, timedelta
from sqlmodel import Session, select
from auth.accountManagment import get_current_user, is_token_valid
from misc import db, schemas, models
from . import travel
from misc import logging, config
import auth
import account
from typing import Optional
import json
from PIL import Image
import io

app = APIRouter(tags=["account"])
config_data = config.config
debug_mode = config_data['app']['debug']
db_name = config_data['app']['nameDB']


@app.get("/user/{user_id}/points")
def user_points(user_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get user points with proper authorization checks.
    Users can only access their own points unless they have admin privileges.
    """
    try:
        roles = current_user.get("roles", [])
        user_id_from_token = current_user.get("sub")
        
        if user_id != user_id_from_token and "admin" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="You can only access your own points unless you have admin privileges."
            )
            
        points = travel.get_user_points(user_id)
        return {"points": points, "user_id": user_id}
    except Exception as e:
        logging.log("Error getting points: " + str(e), "error")
        if debug_mode:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error getting points: " + str(e))
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error getting points")

@app.get("/user/{user_id}/profile")
def get_user_profile(user_id: str, current_user: dict = Depends(get_current_user), session: Session = Depends(db.get_session)):
    """
    Get comprehensive user profile data including personal info, travel stats, and achievements.
    """
    try:
        roles = current_user.get("roles", [])
        user_id_from_token = current_user.get("sub")
        
        # Authorization check
        if user_id != user_id_from_token and "admin" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="You can only access your own profile unless you have admin privileges."
            )
        
        # Get user data
        user = session.exec(select(models.User).where(models.User.id == int(user_id))).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Get user hours data
        user_hours = session.exec(select(models.UserHours).where(models.UserHours.user_id == int(user_id))).first()
        
        # Get travel statistics
        travel_stats = travel.get_user_travel_stats(user_id, "all")
        
        # Calculate achievements
        achievements = calculate_user_achievements(user, user_hours, travel_stats)
        
        # Build profile response
        profile_data = {
            "user_id": user_id,
            "personal_info": {
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "is_active": user.is_active,
                "profile_picture_url": f"/user/{user_id}/picture"
            },
            "points_and_level": {
                "total_points": user.points,
                "level": calculate_user_level(user.points),
                "points_to_next_level": calculate_points_to_next_level(user.points)
            },
            "travel_statistics": travel_stats,
            "achievements": achievements,
            "preferences": get_user_preferences(user_id, session)
        }
        
        return {"success": True, "data": profile_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.log(f"Error getting user profile: {str(e)}", "error")
        if debug_mode:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving profile")

@app.put("/user/{user_id}/profile")
async def update_user_profile(
    user_id: str, 
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    privacy_settings: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    """
    Update user profile information with validation and security checks.
    """
    try:
        roles = current_user.get("roles", [])
        user_id_from_token = current_user.get("sub")
        
        # Authorization check
        if user_id != user_id_from_token and "admin" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="You can only update your own profile unless you have admin privileges."
            )
        
        # Get user
        user = session.exec(select(models.User).where(models.User.id == int(user_id))).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Update fields
        updated_fields = []
        
        if username is not None:
            # Check if username is already taken
            existing_user = session.exec(select(models.User).where(models.User.username == username, models.User.id != int(user_id))).first()
            if existing_user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
            user.username = username
            updated_fields.append("username")
        
        if email is not None:
            # Basic email validation
            if "@" not in email or "." not in email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")
            
            # Check if email is already taken
            existing_user = session.exec(select(models.User).where(models.User.email == email, models.User.id != int(user_id))).first()
            if existing_user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken")
            user.email = email
            updated_fields.append("email")
        
        if bio is not None:
            # Bio length validation
            if len(bio) > 500:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bio too long (max 500 characters)")
            # Store bio in user preferences
            set_user_preference(user_id, "bio", bio, session)
            updated_fields.append("bio")
        
        if privacy_settings is not None:
            try:
                privacy_data = json.loads(privacy_settings)
                set_user_preference(user_id, "privacy_settings", privacy_data, session)
                updated_fields.append("privacy_settings")
            except json.JSONDecodeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid privacy settings format")
        
        # Save changes
        session.add(user)
        session.commit()
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "updated_fields": updated_fields
        }
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logging.log(f"Error updating user profile: {str(e)}", "error")
        if debug_mode:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating profile")

@app.post("/user/{user_id}/picture")
async def upload_profile_picture(
    user_id: str, 
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and process user profile picture with image validation and optimization.
    """
    try:
        roles = current_user.get("roles", [])
        user_id_from_token = current_user.get("sub")
        
        # Authorization check
        if user_id != user_id_from_token and "admin" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="You can only update your own profile picture unless you have admin privileges."
            )
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="File must be an image"
            )
        
        # Check file size (max 5MB)
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="File too large (max 5MB)"
            )
        
        # Create directory if it doesn't exist
        upload_dir = "misc/templates/pfp"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Process and optimize image
        try:
            image = Image.open(io.BytesIO(contents))
            
            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Resize to standard profile picture size
            image.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            # Save optimized image
            file_location = f"{upload_dir}/{user_id}.jpg"
            image.save(file_location, "JPEG", quality=85, optimize=True)
            
        except Exception as img_error:
            logging.log(f"Error processing image: {str(img_error)}", "error")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid image file"
            )
        
        # Update user profile picture timestamp
        session = next(db.get_session())
        user = session.exec(select(models.User).where(models.User.id == int(user_id))).first()
        if user:
            set_user_preference(user_id, "profile_picture_updated", datetime.utcnow().isoformat(), session)
        
        return {
            "success": True,
            "message": "Profile picture uploaded successfully",
            "filename": f"{user_id}.jpg",
            "url": f"/user/{user_id}/picture"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.log(f"Error uploading profile picture: {str(e)}", "error")
        if debug_mode:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error uploading profile picture")

@app.get("/user/{user_id}/picture")
def get_user_picture(user_id: str):
    """
    Get user profile picture with fallback to default image.
    """
    file_location = f"misc/templates/pfp/{user_id}.jpg"
    default_location = f"misc/templates/pfp/default.jpg"
    
    try:
        if os.path.exists(file_location):
            return FileResponse(file_location, media_type="image/jpeg")
        elif os.path.exists(default_location):
            return FileResponse(default_location, media_type="image/jpeg")
        else:
            # Return a simple colored square as fallback
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile picture not found")
    except Exception as e:
        logging.log(f"Error retrieving profile picture for user {user_id}: {str(e)}", "error")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving profile picture")

@app.get("/user/{user_id}/achievements")
def get_user_achievements(user_id: str, current_user: dict = Depends(get_current_user), session: Session = Depends(db.get_session)):
    """
    Get user achievements and badges based on travel activity.
    """
    try:
        roles = current_user.get("roles", [])
        user_id_from_token = current_user.get("sub")
        
        # Authorization check (achievements can be public or private based on user settings)
        if user_id != user_id_from_token and "admin" not in roles:
            # Check if user has public achievements
            privacy_settings = get_user_preference(user_id, "privacy_settings", session)
            if privacy_settings and not privacy_settings.get("achievements_public", True):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="User achievements are private"
                )
        
        # Get user data
        user = session.exec(select(models.User).where(models.User.id == int(user_id))).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        user_hours = session.exec(select(models.UserHours).where(models.UserHours.user_id == int(user_id))).first()
        travel_stats = travel.get_user_travel_stats(user_id, "all")
        
        achievements = calculate_user_achievements(user, user_hours, travel_stats)
        
        return {"success": True, "data": achievements}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.log(f"Error getting user achievements: {str(e)}", "error")
        if debug_mode:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving achievements")

@app.get("/user/{user_id}/preferences")
def get_user_preferences_endpoint(user_id: str, current_user: dict = Depends(get_current_user), session: Session = Depends(db.get_session)):
    """
    Get user preferences and settings.
    """
    try:
        roles = current_user.get("roles", [])
        user_id_from_token = current_user.get("sub")
        
        # Authorization check
        if user_id != user_id_from_token and "admin" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="You can only access your own preferences unless you have admin privileges."
            )
        
        preferences = get_user_preferences(user_id, session)
        
        return {"success": True, "data": preferences}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.log(f"Error getting user preferences: {str(e)}", "error")
        if debug_mode:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving preferences")

@app.put("/user/{user_id}/preferences")
async def update_user_preferences(
    user_id: str,
    preferences: dict,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    """
    Update user preferences and settings.
    """
    try:
        roles = current_user.get("roles", [])
        user_id_from_token = current_user.get("sub")
        
        # Authorization check
        if user_id != user_id_from_token and "admin" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="You can only update your own preferences unless you have admin privileges."
            )
        
        # Update preferences
        for key, value in preferences.items():
            set_user_preference(user_id, key, value, session)
        
        return {
            "success": True,
            "message": "Preferences updated successfully",
            "updated_preferences": list(preferences.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.log(f"Error updating user preferences: {str(e)}", "error")
        if debug_mode:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating preferences")

# Helper functions

def calculate_user_level(points: int) -> int:
    """Calculate user level based on points (100 points per level)."""
    return max(1, points // 100)

def calculate_points_to_next_level(points: int) -> int:
    """Calculate points needed to reach next level."""
    current_level = calculate_user_level(points)
    return (current_level * 100) - points

def calculate_user_achievements(user, user_hours, travel_stats) -> list:
    """Calculate user achievements based on their activity."""
    achievements = []
    
    # Points-based achievements
    if user.points >= 1000:
        achievements.append({"name": "Point Master", "description": "Earned 1000+ points", "icon": "🏆"})
    if user.points >= 5000:
        achievements.append({"name": "Travel Champion", "description": "Earned 5000+ points", "icon": "🥇"})
    
    # Travel time achievements
    if user_hours:
        if user_hours.hoursTotal >= 100:
            achievements.append({"name": "Century Traveler", "description": "100+ hours of travel", "icon": "⏰"})
        if user_hours.hoursTotal >= 500:
            achievements.append({"name": "Travel Veteran", "description": "500+ hours of travel", "icon": "🌟"})
    
    # Travel stats achievements
    if travel_stats:
        trip_count = travel_stats.get("trip_count", 0)
        if trip_count >= 50:
            achievements.append({"name": "Frequent Traveler", "description": "50+ trips completed", "icon": "🚌"})
        if trip_count >= 200:
            achievements.append({"name": "Travel Addict", "description": "200+ trips completed", "icon": "🚀"})
    
    return achievements

def get_user_preferences(user_id: str, session: Session) -> dict:
    """Get user preferences from database."""
    try:
        # In a real implementation, this would query a user_preferences table
        # For now, return default preferences
        return {
            "notifications": {
                "email_notifications": True,
                "push_notifications": True,
                "weekly_summary": True
            },
            "privacy": {
                "profile_public": True,
                "achievements_public": True,
                "stats_public": False
            },
            "app_settings": {
                "dark_mode": False,
                "language": "en",
                "distance_unit": "km"
            }
        }
    except Exception as e:
        logging.log(f"Error getting user preferences: {str(e)}", "error")
        return {}

def get_user_preference(user_id: str, key: str, session: Session):
    """Get a specific user preference."""
    preferences = get_user_preferences(user_id, session)
    return preferences.get(key)

def set_user_preference(user_id: str, key: str, value, session: Session):
    """Set a user preference (placeholder for actual implementation)."""
    # In a real implementation, this would save to a user_preferences table
    pass

# Legacy endpoints for backward compatibility
@app.get("/user/{user_id}/getData")
def user_get_data(user_id: str, token: str = Depends(schemas.Token), session: Session = Depends(db.get_session)):
    """Legacy endpoint - use /user/{user_id}/profile instead."""
    user = account.user_get_data(user_id, session)
    return user

@app.get("/user/{user_id}/getDataHours")
def user_get_data_hours(user_id: str, token: str = Depends(schemas.Token), session: Session = Depends(db.get_session)):
    """Legacy endpoint for user hours data."""
    user = account.user_get_data_hours(user_id, session)
    return user