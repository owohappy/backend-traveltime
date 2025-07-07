from fastapi import APIRouter, Request
from auth.accountManagment import is_token_valid
from misc import schemas
from . import travel
from misc import config
from levels.calcXP import calcXP
from datetime import datetime

app = APIRouter(tags=["travel"])
config_data = config.config
debug_mode = config_data['app']['debug']
base_url = config_data['app']['baseURL']
db_name = config_data['app']['nameDB']

@app.post("/gps/track/{user_id}")
async def track_gps_location(user_id: str, ping: schemas.LocationPing, request: Request):
    """
    Enhanced GPS location tracking endpoint for public transport travel time monitoring.
    
    This endpoint processes GPS coordinates to determine if a user is on public transportation
    and tracks their travel sessions including duration, distance, and transport type.
    
    Args:
        user_id: Unique identifier for the user
        ping: LocationPing containing latitude, longitude, and optional timestamp
        request: FastAPI request object containing authentication headers
    
    Returns:
        JSON response with:
        - travel_status: Current transport status (on_transport/off_transport)
        - session_info: Travel session details (new/continuing/ended/none)
        - duration_seconds: Time spent in current/last session
        - distance_km: Distance traveled in current/last session
        - transport_type: Detected type of transport (bus/train/tram/unknown)
        - location_data: Current GPS coordinates and accuracy
        - xp_awarded: Experience points awarded (if session ended)
        - daily_stats: User's daily travel statistics
    """
    headers = request.headers
    auth = str(headers.get("Authorization", ""))
    
    # Validate authentication token
    if not is_token_valid(auth):
        return {
            "error": "Unauthorized",
            "message": "Invalid or missing authentication token",
            "code": "AUTH_INVALID"
        }
    
    try:
        # Validate input parameters
        if not user_id or not user_id.isdigit():
            return {
                "error": "Invalid user ID",
                "message": "User ID must be a valid numeric string",
                "code": "INVALID_USER_ID"
            }
        
        # Validate GPS coordinates
        if not (-90 <= ping.latitude <= 90):
            return {
                "error": "Invalid latitude",
                "message": "Latitude must be between -90 and 90 degrees",
                "code": "INVALID_LATITUDE"
            }
        
        if not (-180 <= ping.longitude <= 180):
            return {
                "error": "Invalid longitude", 
                "message": "Longitude must be between -180 and 180 degrees",
                "code": "INVALID_LONGITUDE"
            }
        
        # Use provided timestamp or current time
        timestamp = ping.timestamp if hasattr(ping, 'timestamp') and ping.timestamp else None
        
        # Process GPS location with enhanced tracking logic
        tracking_result = travel.gpsinput(user_id, ping.latitude, ping.longitude, timestamp)
        
        # Enhanced response structure
        response_data = {
            "travel_status": "on_transport" if tracking_result.get("on_transport", False) else "off_transport",
            "session_info": {
                "type": tracking_result.get("session_type", "none"),
                "travel_id": tracking_result.get("travel_id"),
                "duration_seconds": tracking_result.get("duration", 0.0),
                "distance_km": round(tracking_result.get("distance", 0.0), 3),
                "transport_type": tracking_result.get("transport_type", "unknown")
            },
            "location_data": {
                "latitude": ping.latitude,
                "longitude": ping.longitude,
                "timestamp": timestamp or datetime.utcnow().isoformat(),
                "on_route": tracking_result.get("on_transport", False)
            },
            "user_id": user_id
        }
        
        # Award XP and update stats for completed travel sessions
        if tracking_result.get("session_type") == "ended" and tracking_result.get("duration", 0) > 0:
            duration_minutes = tracking_result["duration"] / 60
            
            # Only award XP for meaningful travel sessions (≥2 minutes)
            if duration_minutes >= 2:
                try:
                    xp_awarded = calcXP(user_id, duration_minutes)
                    response_data["rewards"] = {
                        "xp_awarded": xp_awarded,
                        "duration_minutes": round(duration_minutes, 2)
                    }
                except Exception as xp_error:
                    if debug_mode:
                        response_data["warnings"] = [f"XP calculation failed: {str(xp_error)}"]
                
                # Get updated daily travel statistics
                try:
                    daily_stats = travel.get_user_travel_stats(user_id, "daily")
                    response_data["daily_stats"] = daily_stats
                except Exception as stats_error:
                    if debug_mode:
                        response_data["warnings"] = response_data.get("warnings", []) + [f"Stats calculation failed: {str(stats_error)}"]
        
        return {
            "success": True,
            "data": response_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as ve:
        return {
            "error": "Invalid input data",
            "message": str(ve),
            "code": "VALIDATION_ERROR"
        }
    except Exception as e:
        error_response = {
            "error": "Server error",
            "code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if debug_mode:
            error_response["detail"] = str(e)
            error_response["type"] = type(e).__name__
        else:
            error_response["message"] = "An internal server error occurred. Please try again later."
            
        return error_response


@app.post("/heartbeat/{user_id}")
async def heartbeat(user_id: str, ping: schemas.LocationPing, request: Request):
    """
    Legacy GPS heartbeat endpoint - redirects to new tracking endpoint.
    
    DEPRECATED: Use /gps/track/{user_id} instead for better functionality.
    This endpoint is maintained for backwards compatibility.
    """
    # Redirect to the new enhanced endpoint
    return await track_gps_location(user_id, ping, request)

@app.get("/travel/stats/{user_id}")
async def get_travel_statistics(user_id: str, timeframe: str = "daily", request: Request = None):
    """
    Get user travel statistics for different timeframes.
    
    Args:
        user_id: User identifier
        timeframe: One of 'daily', 'weekly', 'monthly', 'all'
        request: FastAPI request object for headers
        
    Returns:
        JSON response with travel statistics
    """
    headers = request.headers if request else {}
    auth = str(headers.get("Authorization", ""))
    
    if not is_token_valid(auth):
        return {"error": "Invalid JWT"}
    
    try:
        if timeframe not in ["daily", "weekly", "monthly", "all"]:
            return {"error": "Invalid timeframe. Use 'daily', 'weekly', 'monthly', or 'all'"}
        
        stats = travel.get_user_travel_stats(user_id, timeframe)
        return {"success": True, "data": stats}
        
    except Exception as e:
        if debug_mode:
            return {"error": "Server error", "detail": str(e)}
        else:
            return {"error": "Server error occurred"}

@app.get("/travel/history/{user_id}")
async def get_travel_history(user_id: str, limit: int = 10, request: Request = None):
    """
    Get user's recent travel history.
    
    Args:
        user_id: User identifier
        limit: Number of recent trips to return (default 10, max 50)
        request: FastAPI request object for headers
        
    Returns:
        JSON response with travel history
    """
    headers = request.headers if request else {}
    auth = str(headers.get("Authorization", ""))
    
    if not is_token_valid(auth):
        return {"error": "Invalid JWT"}
    
    try:
        from misc.db import get_session
        from misc.models import TravelHistory
        from sqlmodel import select
        
        # Limit the number of results to prevent abuse
        limit = min(max(1, limit), 50)
        
        with get_session() as session:
            statement = select(TravelHistory).where(
                TravelHistory.user_id == int(user_id),
                TravelHistory.duration > 120  # Only show trips longer than 2 minutes
            ).order_by(TravelHistory.timestamp.desc()).limit(limit)
            
            travels = session.exec(statement).all()
            
            travel_data = []
            for travel in travels:
                travel_data.append({
                    "id": travel.id,
                    "timestamp": travel.timestamp.isoformat(),
                    "duration_minutes": round(travel.duration / 60, 2),
                    "distance_km": round(travel.distance, 2),
                    "start_location": {
                        "latitude": travel.startLatitude,
                        "longitude": travel.startLongitude
                    },
                    "route_points": len(travel.listLatitude) if travel.listLatitude else 1
                })
            
            return {"success": True, "data": {
                "travels": travel_data,
                "total_count": len(travel_data)
            }}
            
    except Exception as e:
        if debug_mode:
            return {"error": "Server error", "detail": str(e)}
        else:
            return {"error": "Server error occurred"}

@app.get("/gps/status/{user_id}")
async def get_tracking_status(user_id: str, request: Request):
    """
    Get current GPS tracking status for a user without submitting new location data.
    
    This endpoint retrieves the user's current travel session status, including
    any active transportation usage and recent travel statistics.
    
    Args:
        user_id: Unique identifier for the user
        request: FastAPI request object containing authentication headers
    
    Returns:
        JSON response with current tracking status and travel statistics
    """
    headers = request.headers
    auth = str(headers.get("Authorization", ""))
    
    if not is_token_valid(auth):
        return {
            "error": "Unauthorized",
            "message": "Invalid or missing authentication token",
            "code": "AUTH_INVALID"
        }
    
    try:
        if not user_id or not user_id.isdigit():
            return {
                "error": "Invalid user ID",
                "message": "User ID must be a valid numeric string",
                "code": "INVALID_USER_ID"
            }
        
        from misc.db import get_session
        from misc.models import TravelHistory, User
        from sqlmodel import select
        from datetime import datetime, timedelta
        
        with get_session() as session:
            # Verify user exists
            user_statement = select(User).where(User.id == int(user_id))
            user = session.exec(user_statement).first()
            if not user:
                return {
                    "error": "User not found",
                    "message": f"User with ID {user_id} does not exist",
                    "code": "USER_NOT_FOUND"
                }
            
            # Get most recent travel session
            statement = select(TravelHistory).where(
                TravelHistory.user_id == int(user_id)
            ).order_by(TravelHistory.timestamp.desc()).limit(1)
            
            last_travel = session.exec(statement).first()
            
            # Determine current status
            now = datetime.utcnow()
            is_active_session = False
            session_data = None
            
            if last_travel:
                time_since_last = (now - last_travel.timestamp).total_seconds()
                
                # Consider session active if within 10 minutes and has valid duration
                if time_since_last <= 600 and last_travel.duration > 0:
                    is_active_session = True
                    session_data = {
                        "travel_id": last_travel.id,
                        "start_time": last_travel.timestamp.isoformat(),
                        "duration_seconds": last_travel.duration,
                        "distance_km": round(last_travel.distance, 3),
                        "start_location": {
                            "latitude": last_travel.startLatitude,
                            "longitude": last_travel.startLongitude
                        },
                        "route_points": len(last_travel.listLatitude) if last_travel.listLatitude else 1
                    }
            
            # Get travel statistics for different timeframes
            daily_stats = travel.get_user_travel_stats(user_id, "daily")
            weekly_stats = travel.get_user_travel_stats(user_id, "weekly")
            monthly_stats = travel.get_user_travel_stats(user_id, "monthly")
            
            response_data = {
                "user_id": user_id,
                "tracking_status": {
                    "is_active_session": is_active_session,
                    "current_session": session_data,
                    "last_activity": last_travel.timestamp.isoformat() if last_travel else None
                },
                "travel_statistics": {
                    "daily": daily_stats,
                    "weekly": weekly_stats,
                    "monthly": monthly_stats
                },
                "user_profile": {
                    "name": user.name,
                    "total_xp": user.xp,
                    "level": user.level,
                    "total_points": user.points
                }
            }
            
            return {
                "success": True,
                "data": response_data,
                "timestamp": now.isoformat()
            }
            
    except Exception as e:
        error_response = {
            "error": "Server error",
            "code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if debug_mode:
            error_response["detail"] = str(e)
            error_response["type"] = type(e).__name__
        else:
            error_response["message"] = "An internal server error occurred. Please try again later."
            
        return error_response


@app.get("/gps/routes/nearby")
async def get_nearby_routes(latitude: float, longitude: float, radius: int = 1000, request: Request = None):
    """
    Get nearby public transportation routes for given GPS coordinates.
    
    This endpoint helps clients understand what transport options are available
    near a specific location and can be used for route planning.
    
    Args:
        latitude: GPS latitude coordinate (-90 to 90)
        longitude: GPS longitude coordinate (-180 to 180)  
        radius: Search radius in meters (default: 1000, max: 5000)
        request: FastAPI request object for authentication
    
    Returns:
        JSON response with nearby transportation routes
    """
    headers = request.headers if request else {}
    auth = str(headers.get("Authorization", ""))
    
    if not is_token_valid(auth):
        return {
            "error": "Unauthorized", 
            "message": "Invalid or missing authentication token",
            "code": "AUTH_INVALID"
        }
    
    try:
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            return {
                "error": "Invalid latitude",
                "message": "Latitude must be between -90 and 90 degrees",
                "code": "INVALID_LATITUDE"
            }
        
        if not (-180 <= longitude <= 180):
            return {
                "error": "Invalid longitude",
                "message": "Longitude must be between -180 and 180 degrees", 
                "code": "INVALID_LONGITUDE"
            }
        
        # Limit radius to reasonable bounds
        radius = max(50, min(radius, 5000))
        
        # Get nearby routes using the travel module
        nearby_routes = travel.get_nearby_routes(latitude, longitude, radius_meters=radius)
        
        # Check if user would be considered "on route" at this location
        on_route = travel.is_user_on_any_nearby_route(latitude, longitude)
        
        # Detect likely transport type
        transport_type = travel.detect_transport_type(latitude, longitude)
        
        response_data = {
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "search_radius_meters": radius
            },
            "route_analysis": {
                "nearby_routes_count": len(nearby_routes),
                "on_transport_route": on_route,
                "detected_transport_type": transport_type
            },
            "routes": [
                {
                    "route_id": idx,
                    "coordinates_count": len(route.coords) if hasattr(route, 'coords') else 0,
                    "route_length_km": round(route.length * 111.32, 2) if hasattr(route, 'length') else 0
                }
                for idx, route in enumerate(nearby_routes[:20])  # Limit to first 20 routes
            ]
        }
        
        return {
            "success": True,
            "data": response_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        error_response = {
            "error": "Server error",
            "code": "INTERNAL_ERROR", 
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if debug_mode:
            error_response["detail"] = str(e)
            error_response["type"] = type(e).__name__
        else:
            error_response["message"] = "An internal server error occurred. Please try again later."
            
        return error_response


@app.post("/admin/routes/refresh")
async def refresh_route_cache(request: Request):
    """
    Admin endpoint to refresh the route cache.
    
    This endpoint forces a refresh of the transportation route data from all
    configured APIs and rebuilds the spatial index for better performance.
    
    Args:
        request: FastAPI request object containing authentication headers
    
    Returns:
        JSON response with cache refresh status
    """
    headers = request.headers
    auth = str(headers.get("Authorization", ""))
    
    if not is_token_valid(auth):
        return {
            "error": "Unauthorized",
            "message": "Invalid or missing authentication token",
            "code": "AUTH_INVALID"
        }
    
    try:
        # Force refresh the route cache
        start_time = datetime.utcnow()
        travel.route_manager.refresh_cache()
        end_time = datetime.utcnow()
        
        refresh_duration = (end_time - start_time).total_seconds()
        route_count = travel.route_manager.get_routes_count()
        
        return {
            "success": True,
            "data": {
                "refresh_duration_seconds": refresh_duration,
                "total_routes_loaded": route_count,
                "cache_updated": end_time.isoformat(),
                "spatial_index_rebuilt": True
            },
            "timestamp": end_time.isoformat()
        }
        
    except Exception as e:
        error_response = {
            "error": "Server error",
            "code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if debug_mode:
            error_response["detail"] = str(e)
            error_response["type"] = type(e).__name__
        else:
            error_response["message"] = "Failed to refresh route cache. Please try again later."
            
        return error_response


@app.get("/admin/routes/status")
async def get_route_cache_status(request: Request):
    """
    Admin endpoint to get route cache status and statistics.
    
    Args:
        request: FastAPI request object containing authentication headers
    
    Returns:
        JSON response with route cache status and performance metrics
    """
    headers = request.headers
    auth = str(headers.get("Authorization", ""))
    
    if not is_token_valid(auth):
        return {
            "error": "Unauthorized",
            "message": "Invalid or missing authentication token", 
            "code": "AUTH_INVALID"
        }
    
    try:
        import os
        
        cache_file = travel.CACHE_FILE
        cache_exists = os.path.exists(cache_file)
        cache_size = 0
        cache_modified = None
        
        if cache_exists:
            cache_size = os.path.getsize(cache_file)
            cache_modified = datetime.fromtimestamp(os.path.getmtime(cache_file))
        
        # Get route manager stats
        route_count = travel.route_manager.get_routes_count() if travel.route_manager._loaded else 0
        is_loaded = travel.route_manager._loaded
        spatial_index_size = len(travel.route_manager._spatial_index) if is_loaded else 0
        
        response_data = {
            "cache_status": {
                "file_exists": cache_exists,
                "file_size_bytes": cache_size,
                "file_size_mb": round(cache_size / (1024 * 1024), 2),
                "last_modified": cache_modified.isoformat() if cache_modified else None,
                "age_hours": round((datetime.utcnow() - cache_modified).total_seconds() / 3600, 1) if cache_modified else None
            },
            "route_manager": {
                "routes_loaded": is_loaded,
                "total_routes": route_count,
                "spatial_index_cells": spatial_index_size,
                "memory_usage_estimated_mb": round((route_count * 0.5 + spatial_index_size * 0.1), 2)
            },
            "performance": {
                "cache_file_path": cache_file,
                "lazy_loading_enabled": True,
                "spatial_indexing_enabled": True
            }
        }
        
        return {
            "success": True,
            "data": response_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        error_response = {
            "error": "Server error",
            "code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if debug_mode:
            error_response["detail"] = str(e)
            error_response["type"] = type(e).__name__
        else:
            error_response["message"] = "Failed to get route status. Please try again later."
            
        return error_response
