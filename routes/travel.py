from fastapi import APIRouter, Request
from auth.accountManagment import is_token_valid
from misc import schemas
from misc.schemas import ManualRideLog
from misc.models import ManualRide
from misc.db import get_session
import travel
from misc import config, db, models
from levels.calcXP import calcXP
from datetime import datetime
from sqlmodel import Session, select
import json
from collections import defaultdict
import statistics

app = APIRouter(tags=["travel"])
config_data = config.config
debug_mode = config_data['app']['debug']
base_url = config_data['app']['baseURL']
db_name = config_data['app']['nameDB']

@app.post("/gps/track/{user_id}")
async def track_gps_location(user_id: str, ping: schemas.LocationPing, request: Request):
    """Track user's GPS location and detect if they're on public transport."""
    headers = request.headers
    auth = str(headers.get("Authorization", ""))
    
    if not is_token_valid(auth):
        return {"error": "Unauthorized"}
    
    try:
        # Basic validation
        if not user_id or not user_id.isdigit():
            return {"error": "Invalid user ID"}
        
        if not (-90 <= ping.latitude <= 90) or not (-180 <= ping.longitude <= 180):
            return {"error": "Invalid coordinates"}
        
        # Process the GPS ping
        timestamp = ping.timestamp if hasattr(ping, 'timestamp') and ping.timestamp else None
        result = travel.gpsinput(user_id, ping.latitude, ping.longitude, timestamp)
        
        # Update analytics if we detected transport
        if result.get("on_transport", False):
            route_id = result.get("route_id")
            transport_type = result.get("transport_type")
            operator = result.get("operator")
            
            if route_id:
                travel.route_analytics.update_route_usage(route_id, transport_type, operator)
                
                # Learn from this trip if it's active
                if result.get("session_type") in ["new", "continuing"]:
                    speed = result.get("speed_kmh", 0)
                    if speed > 0:
                        travel.route_analytics.learn_transport_pattern(
                            transport_type or "unknown",
                            [speed],
                            result.get("stop_frequency", 0.5),
                            result.get("route_geometry", "")
                        )
        
        # Build response
        response_data = {
            "travel_status": "on_transport" if result.get("on_transport", False) else "off_transport",
            "session_info": {
                "type": result.get("session_type", "none"),
                "travel_id": result.get("travel_id"),
                "duration_seconds": result.get("duration", 0.0),
                "distance_km": round(result.get("distance", 0.0), 3),
                "transport_type": result.get("transport_type", "unknown")
            },
            "location_data": {
                "latitude": ping.latitude,
                "longitude": ping.longitude,
                "timestamp": timestamp or datetime.utcnow().isoformat(),
                "on_route": result.get("on_transport", False)
            },
            "user_id": user_id
        }
        
        # Award XP if trip ended
        if result.get("session_type") == "ended" and result.get("duration", 0) > 0:
            duration_minutes = result["duration"] / 60
            
            if duration_minutes >= 2:  # Only meaningful trips
                try:
                    xp = calcXP(user_id, duration_minutes)
                    response_data["xp_awarded"] = xp
                except Exception:
                    pass  # XP calculation failed, no big deal
                
                try:
                    daily_stats = travel.get_user_travel_stats(user_id, "daily")
                    response_data["daily_stats"] = daily_stats
                except Exception:
                    pass  # Stats failed, whatever
        
        return {"success": True, "data": response_data}
        
    except Exception as e:
        if debug_mode:
            return {"error": f"Server error: {str(e)}"}
        return {"error": "Something went wrong"}


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
            "message": "Invalid or missing token",
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
            "message": "Invalid or missing token",
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
            "message": "Invalid or missing token",
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
            "message": "Invalid or missing token", 
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


# Import additional modules for analytics
from misc import models
from sqlmodel import Session, select
import json
from collections import defaultdict
import statistics

@app.get("/analytics/popular-routes")
async def get_popular_routes(request: Request, limit: int = 10):
    """Get the most popular bus/train routes."""
    if not is_token_valid(str(request.headers.get("Authorization", ""))):
        return {"error": "Unauthorized"}
    
    try:
        limit = min(max(1, limit), 50)  # Between 1 and 50
        popular_routes = travel.route_analytics.get_popular_routes(limit)
        
        routes = []
        for route_id, usage_count in popular_routes:
            route_info = travel.route_analytics.get_route_analytics(route_id)
            
            # Try to get route details
            route_details = None
            if travel.route_manager._loaded:
                for route in travel.route_manager.routes:
                    if route.get('id') == route_id:
                        route_details = {
                            "name": route.get('name', 'Unknown Route'),
                            "transport_type": route.get('transport_type', 'unknown'),
                            "operator": route.get('operator', 'unknown')
                        }
                        break
            
            routes.append({
                "route_id": route_id,
                "usage_count": usage_count,
                "route_details": route_details,
                "confidence": route_info.get("confidence", 0.0)
            })
        
        return {"routes": routes, "total_analyzed": len(travel.route_analytics.route_usage_stats)}
        
    except Exception as e:
        return {"error": f"Failed to get routes: {str(e)}" if debug_mode else "Server error"}

@app.get("/analytics/operator-stats")
async def get_operator_stats(request: Request):
    """Get stats on different transport operators."""
    if not is_token_valid(str(request.headers.get("Authorization", ""))):
        return {"error": "Unauthorized"}
    
    try:
        operator_stats = travel.route_analytics.get_operator_stats()
        total_routes = sum(sum(types.values()) for types in operator_stats.values())
        
        operators = []
        for operator, transport_types in operator_stats.items():
            operator_routes = sum(transport_types.values())
            operators.append({
                "operator": operator,
                "routes": operator_routes,
                "types": dict(transport_types),
                "share": round(operator_routes / total_routes * 100, 1) if total_routes > 0 else 0
            })
        
        operators.sort(key=lambda x: x['routes'], reverse=True)
        
        # Transport type totals
        type_totals = defaultdict(int)
        for types in operator_stats.values():
            for transport_type, count in types.items():
                type_totals[transport_type] += count
        
        return {
            "operators": operators,
            "transport_types": dict(type_totals),
            "total_routes": total_routes
        }
        
    except Exception as e:
        return {"error": f"Failed: {str(e)}" if debug_mode else "Server error"}

@app.get("/analytics/transport-patterns")
async def get_transport_patterns(request: Request):
    """
    Get learned transport patterns and type detection analytics.
    
    Args:
        request: FastAPI request object containing authentication headers
    
    Returns:
        JSON response with transport patterns, detection accuracy, and learning statistics
    """
    headers = request.headers
    auth = str(headers.get("Authorization", ""))
    
    if not is_token_valid(auth):
        return {
            "error": "Unauthorized",
            "message": "Invalid or missing token",
            "code": "AUTH_INVALID"
        }
    
    try:
        # Get transport patterns from analytics
        transport_patterns = {}
        
        for transport_type, pattern in travel.route_analytics.transport_patterns.items():
            # Calculate pattern statistics
            speed_stats = {}
            if pattern.speed_profile:
                speed_stats = {
                    "avg_speed": round(statistics.mean(pattern.speed_profile), 2),
                    "speed_variance": round(statistics.variance(pattern.speed_profile), 2) if len(pattern.speed_profile) > 1 else 0,
                    "min_speed": round(min(pattern.speed_profile), 2),
                    "max_speed": round(max(pattern.speed_profile), 2),
                    "data_points": len(pattern.speed_profile)
                }
            
            transport_patterns[transport_type] = {
                "confidence": round(pattern.confidence, 3),
                "sample_count": pattern.sample_count,
                "stop_frequency": round(pattern.stop_frequency, 3),
                "speed_statistics": speed_stats,
                "learning_status": "active" if pattern.confidence > 0.5 else "learning"
            }
        
        # Calculate overall detection accuracy
        total_samples = sum(p.sample_count for p in travel.route_analytics.transport_patterns.values())
        high_confidence_patterns = sum(1 for p in travel.route_analytics.transport_patterns.values() if p.confidence > 0.7)
        
        detection_accuracy = {
            "total_transport_types": len(transport_patterns),
            "high_confidence_patterns": high_confidence_patterns,
            "total_learning_samples": total_samples,
            "overall_confidence": round(statistics.mean([p.confidence for p in travel.route_analytics.transport_patterns.values()]), 3) if transport_patterns else 0
        }
        
        return {
            "success": True,
            "data": {
                "transport_patterns": transport_patterns,
                "detection_accuracy": detection_accuracy,
                "learning_enabled": True
            },
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
            error_response["message"] = "Failed to get transport patterns. Please try again later."
            
        return error_response

@app.get("/analytics/user/{user_id}/travel-insights")
async def get_user_travel_insights(user_id: str, request: Request):
    """
    Get personalized travel insights and analytics for a specific user.
    
    Args:
        user_id: User ID to get travel insights for
        request: FastAPI request object containing authentication headers
    
    Returns:
        JSON response with user travel patterns, preferences, and personalized analytics
    """
    headers = request.headers
    auth = str(headers.get("Authorization", ""))
    
    if not is_token_valid(auth):
        return {
            "error": "Unauthorized",
            "message": "Invalid or missing token",
            "code": "AUTH_INVALID"
        }
    
    try:
        # Validate user ID
        if not user_id or not user_id.isdigit():
            return {
                "error": "Invalid user ID",
                "message": "User ID must be a valid numeric string",
                "code": "INVALID_USER_ID"
            }
        
        # Get user travel data from database
        session = next(db.get_session())
        
        # Query user's travel sessions
        user_travels = session.exec(
            select(models.Travel).where(models.Travel.user_id == int(user_id))
        ).all()
        
        if not user_travels:
            return {
                "success": True,
                "data": {
                    "user_id": user_id,
                    "travel_insights": {},
                    "message": "No travel data found for this user"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Convert to dictionary format for analysis
        travel_data = []
        for travel in user_travels:
            travel_data.append({
                "transport_type": travel.transport_type or "unknown",
                "distance": travel.distance or 0,
                "duration": travel.duration or 0,
                "avg_speed": (travel.distance / (travel.duration / 3600)) if travel.duration and travel.distance else 0,
                "timestamp": travel.timestamp.isoformat() if travel.timestamp else None
            })
        
        # Analyze travel patterns
        patterns = travel.route_analytics.analyze_transport_patterns(travel_data)
        
        # Calculate user-specific statistics
        total_distance = sum(t["distance"] for t in travel_data)
        total_duration = sum(t["duration"] for t in travel_data)
        total_trips = len(travel_data)
        
        # Transport type preferences
        transport_usage = defaultdict(int)
        for travel in travel_data:
            transport_usage[travel["transport_type"]] += 1
        
        preferred_transport = max(transport_usage.items(), key=lambda x: x[1]) if transport_usage else ("unknown", 0)
        
        # Calculate insights
        insights = {
            "travel_summary": {
                "total_trips": total_trips,
                "total_distance_km": round(total_distance, 2),
                "total_duration_hours": round(total_duration / 3600, 2),
                "avg_trip_distance": round(total_distance / total_trips, 2) if total_trips > 0 else 0,
                "avg_trip_duration": round(total_duration / total_trips, 2) if total_trips > 0 else 0
            },
            "transport_preferences": {
                "preferred_transport": preferred_transport[0],
                "usage_distribution": dict(transport_usage),
                "transport_diversity": len(transport_usage)
            },
            "travel_patterns": patterns,
            "efficiency_metrics": {
                "avg_speed_kmh": round(total_distance / (total_duration / 3600), 2) if total_duration > 0 else 0,
                "trips_per_pattern": {transport_type: data["trip_count"] for transport_type, data in patterns.items()},
                "consistency_score": round(statistics.mean([data["pattern_confidence"] for data in patterns.values()]), 3) if patterns else 0
            }
        }
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "travel_insights": insights,
                "data_quality": {
                    "sample_size": total_trips,
                    "reliability": "high" if total_trips > 10 else "medium" if total_trips > 5 else "low"
                }
            },
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
            error_response["message"] = "Failed to get user travel insights. Please try again later."
            
        return error_response

@app.get("/analytics/dashboard")
async def get_analytics_dashboard(request: Request):
    """Get analytics dashboard for admin monitoring."""
    headers = request.headers
    auth = str(headers.get("Authorization", ""))
    
    if not is_token_valid(auth):
        return {
            "error": "Unauthorized",
            "message": "Invalid or missing token",
            "code": "AUTH_INVALID"
        }
    
    try:
        # Get all analytics data
        popular_routes = travel.route_analytics.get_popular_routes(5)
        operator_stats = travel.route_analytics.get_operator_stats()
        
        # Route cache statistics
        route_count = travel.route_manager.get_routes_count() if travel.route_manager._loaded else 0
        cache_loaded = travel.route_manager._loaded
        
        # Transport pattern statistics
        transport_patterns = travel.route_analytics.transport_patterns
        total_samples = sum(p.sample_count for p in transport_patterns.values())
        high_confidence = sum(1 for p in transport_patterns.values() if p.confidence > 0.7)
        
        # Usage statistics
        total_route_usage = sum(travel.route_analytics.route_usage_stats.values())
        unique_routes_used = len(travel.route_analytics.route_usage_stats)
        
        # Calculate system health metrics
        system_health = {
            "route_cache_status": "healthy" if cache_loaded and route_count > 0 else "degraded",
            "analytics_status": "active" if total_samples > 0 else "learning",
            "detection_accuracy": round(high_confidence / len(transport_patterns) * 100, 1) if transport_patterns else 0
        }
        
        # Recent activity (mock data - in production this would come from real activity logs)
        recent_activity = {
            "routes_accessed_last_hour": min(total_route_usage, 50),  # Simulated
            "new_patterns_learned": sum(1 for p in transport_patterns.values() if p.sample_count > 0),
            "cache_hits": total_route_usage
        }
        
        dashboard_data = {
            "system_overview": {
                "total_routes": route_count,
                "routes_cached": cache_loaded,
                "unique_routes_used": unique_routes_used,
                "total_usage_events": total_route_usage,
                "system_health": system_health
            },
            "popular_routes": [
                {
                    "route_id": route_id,
                    "usage_count": usage_count,
                    "percentage": round(usage_count / total_route_usage * 100, 2) if total_route_usage > 0 else 0
                }
                for route_id, usage_count in popular_routes
            ],
            "transport_analytics": {
                "total_operators": len(operator_stats),
                "transport_types_detected": len(transport_patterns),
                "high_confidence_patterns": high_confidence,
                "total_learning_samples": total_samples
            },
            "recent_activity": recent_activity,
            "performance_metrics": {
                "cache_efficiency": round(total_route_usage / route_count * 100, 2) if route_count > 0 else 0,
                "pattern_learning_rate": round(total_samples / max(len(transport_patterns), 1), 1),
                "route_coverage": round(unique_routes_used / route_count * 100, 2) if route_count > 0 else 0
            }
        }
        
        return {
            "success": True,
            "data": dashboard_data,
            "timestamp": datetime.utcnow().isoformat(),
            "refresh_interval": 300  # Recommend refresh every 5 minutes
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
            error_response["message"] = "Failed to get analytics dashboard. Please try again later."
            
        return error_response

from misc.models import ManualRide
from misc.schemas import ManualRideLog
from misc.db import get_session
from fastapi import Depends

@app.post("/rides/manual")
async def log_manual_ride(
    ride: ManualRideLog,
    request: Request
):
    """Log a manual ride entry for the authenticated user."""
    headers = request.headers
    auth = str(headers.get("Authorization", ""))
    
    # Validate JWT and extract user_id
    if not is_token_valid(auth.replace("Bearer ", "")):
        return {"success": False, "error": "Unauthorized"}
    
    try:
        # Extract user_id from JWT using existing function
        from auth.accountManagment import decode_access_token
        payload = decode_access_token(auth.replace("Bearer ", ""))
        if not payload:
            return {"success": False, "error": "Invalid token"}
        
        # Extract user_id from 'sub' field (format: "user_id" + "a")
        sub = payload.get("sub")
        if not sub or not sub.endswith("a"):
            return {"success": False, "error": "Invalid token format"}
        
        user_id = int(sub[:-1])  # Remove the 'a' suffix
        
    except Exception as e:
        return {"success": False, "error": f"Invalid token: {str(e)}"}
    
    try:
        with get_session() as session:
            manual_ride = ManualRide(
                user_id=user_id,
                transport_type=ride.transport_type,
                start_location=ride.start_location,
                end_location=ride.end_location,
                duration_minutes=ride.duration_minutes,
                distance_km=ride.distance_km,
                date=ride.date,
                time=ride.time,
                notes=ride.notes,
                manual_entry=ride.manual_entry
            )
            session.add(manual_ride)
            session.commit()
            session.refresh(manual_ride)
            
            # Calculate and award XP for manual rides if duration is significant
            if ride.duration_minutes >= 2:
                try:
                    xp = calcXP(str(user_id), ride.duration_minutes)
                    return {"success": True, "ride_id": manual_ride.id, "xp_awarded": xp}
                except Exception:
                    return {"success": True, "ride_id": manual_ride.id}
            
            return {"success": True, "ride_id": manual_ride.id}
            
    except Exception as e:
        if debug_mode:
            return {"success": False, "error": f"Failed to log manual ride: {str(e)}"}
        return {"success": False, "error": "Failed to log manual ride. Please try again."}

@app.get("/rides/manual/{user_id}")
async def get_manual_rides(user_id: str, limit: int = 10, request: Request = None):
    """Get manual ride history for a user."""
    headers = request.headers if request else {}
    auth = str(headers.get("Authorization", ""))
    
    if not is_token_valid(auth.replace("Bearer ", "")):
        return {"error": "Unauthorized"}
    
    try:
        # Check user access
        from auth.accountManagment import decode_access_token
        payload = decode_access_token(auth.replace("Bearer ", ""))
        if not payload:
            return {"error": "Invalid token"}
        
        # Extract user_id from 'sub' field (format: "user_id" + "a")
        sub = payload.get("sub")
        if not sub or not sub.endswith("a"):
            return {"error": "Invalid token format"}
        
        request_user_id = int(sub[:-1])  # Remove the 'a' suffix
        
        # Only allow users to access their own data or admin access
        if str(request_user_id) != user_id:
            return {"error": "Access denied"}
        
        # Limit the number of results
        limit = min(max(1, limit), 50)
        
        with get_session() as session:
            statement = select(ManualRide).where(
                ManualRide.user_id == int(user_id)
            ).order_by(ManualRide.created_at.desc()).limit(limit)
            
            rides = session.exec(statement).all()
            
            ride_data = []
            for ride in rides:
                ride_data.append({
                    "id": ride.id,
                    "transport_type": ride.transport_type,
                    "start_location": ride.start_location,
                    "end_location": ride.end_location,
                    "duration_minutes": ride.duration_minutes,
                    "distance_km": ride.distance_km,
                    "date": ride.date,
                    "time": ride.time,
                    "notes": ride.notes,
                    "manual_entry": ride.manual_entry,
                    "created_at": ride.created_at.isoformat()
                })
            
            return {"success": True, "data": {
                "rides": ride_data,
                "total_count": len(ride_data)
            }}
            
    except Exception as e:
        if debug_mode:
            return {"error": f"Server error: {str(e)}"}
        return {"error": "Failed to retrieve manual rides"}

@app.delete("/rides/manual/{ride_id}")
async def delete_manual_ride(ride_id: int, request: Request):
    """Delete a manual ride entry."""
    headers = request.headers
    auth = str(headers.get("Authorization", ""))
    
    if not is_token_valid(auth.replace("Bearer ", "")):
        return {"success": False, "error": "Unauthorized"}
    
    try:
        # Validate token and extract user_id
        from auth.accountManagment import decode_access_token
        payload = decode_access_token(auth.replace("Bearer ", ""))
        if not payload:
            return {"success": False, "error": "Invalid token"}
        
        # Extract user_id from 'sub' field (format: "user_id" + "a")
        sub = payload.get("sub")
        if not sub or not sub.endswith("a"):
            return {"success": False, "error": "Invalid token format"}
        
        user_id = int(sub[:-1])  # Remove the 'a' suffix
        
        with get_session() as session:
            # Find the ride and verify ownership
            statement = select(ManualRide).where(
                ManualRide.id == ride_id,
                ManualRide.user_id == user_id
            )
            ride = session.exec(statement).first()
            
            if not ride:
                return {"success": False, "error": "Ride not found or access denied"}
            
            session.delete(ride)
            session.commit()
            
            return {"success": True, "message": "Manual ride deleted successfully"}
            
    except Exception as e:
        if debug_mode:
            return {"success": False, "error": f"Failed to delete manual ride: {str(e)}"}
        return {"success": False, "error": "Failed to delete manual ride. Please try again."}

@app.put("/rides/manual/{ride_id}")
async def update_manual_ride(ride_id: int, ride: ManualRideLog, request: Request):
    """Update a manual ride entry."""
    headers = request.headers
    auth = str(headers.get("Authorization", ""))
    
    if not is_token_valid(auth.replace("Bearer ", "")):
        return {"success": False, "error": "Unauthorized"}
    
    try:
        # Validate token and extract user_id
        from auth.accountManagment import decode_access_token
        payload = decode_access_token(auth.replace("Bearer ", ""))
        if not payload:
            return {"success": False, "error": "Invalid token"}
        
        # Extract user_id from 'sub' field (format: "user_id" + "a")
        sub = payload.get("sub")
        if not sub or not sub.endswith("a"):
            return {"success": False, "error": "Invalid token format"}
        
        user_id = int(sub[:-1])  # Remove the 'a' suffix
        
        with get_session() as session:
            # Find the ride and verify ownership
            statement = select(ManualRide).where(
                ManualRide.id == ride_id,
                ManualRide.user_id == user_id
            )
            existing_ride = session.exec(statement).first()
            
            if not existing_ride:
                return {"success": False, "error": "Ride not found or access denied"}
            
            # Update the ride with new data
            existing_ride.transport_type = ride.transport_type
            existing_ride.start_location = ride.start_location
            existing_ride.end_location = ride.end_location
            existing_ride.duration_minutes = ride.duration_minutes
            existing_ride.distance_km = ride.distance_km
            existing_ride.date = ride.date
            existing_ride.time = ride.time
            existing_ride.notes = ride.notes
            existing_ride.manual_entry = ride.manual_entry
            
            session.add(existing_ride)
            session.commit()
            session.refresh(existing_ride)
            
            return {"success": True, "ride_id": existing_ride.id, "message": "Manual ride updated successfully"}
            
    except Exception as e:
        if debug_mode:
            return {"success": False, "error": f"Failed to update manual ride: {str(e)}"}
        return {"success": False, "error": "Failed to update manual ride. Please try again."}
