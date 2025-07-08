import requests
from shapely.geometry import Point, LineString, Polygon
import time
import json
import os
import math 
import zipfile
import io
from urllib.parse import quote
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Union, Any
import threading
import hashlib
import statistics
import numpy as np
from datetime import datetime, timedelta
import pickle
import sqlite3

CACHE_FILE = "cached_routes.json"
ANALYTICS_CACHE_FILE = "route_analytics.pkl"
TRANSPORT_PATTERNS_FILE = "transport_patterns.db"

@dataclass
class RouteMetadata:
    """Enhanced route metadata for better transport type detection"""
    route_id: str
    transport_type: str = "unknown"
    operator: str = "unknown"
    route_name: str = ""
    frequency_minutes: Optional[int] = None
    stops: List[Tuple[float, float]] = field(default_factory=list)
    speed_kmh: Optional[float] = None
    usage_count: int = 0
    confidence_score: float = 0.0
    geometry_hash: str = ""
    
@dataclass
class TransportTypePattern:
    """Pattern data for transport type detection"""
    speed_profile: List[float] = field(default_factory=list)
    stop_frequency: float = 0.0
    route_geometry: str = ""
    confidence: float = 0.0
    sample_count: int = 0

def decode_polyline(polyline_str):
    """
    Decode Google's polyline algorithm to get coordinates.
    
    Args:
        polyline_str: Encoded polyline string
        
    Returns:
        List of (lat, lon) tuples
    """
    if not polyline_str:
        return []
    
    index = 0
    lat = 0
    lng = 0
    coordinates = []
    
    while index < len(polyline_str):
        # Decode latitude
        result = 1
        shift = 0
        while True:
            b = ord(polyline_str[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1f:
                break
        lat += (~result >> 1) if (result & 1) != 0 else (result >> 1)
        
        # Decode longitude
        result = 1
        shift = 0
        while True:
            b = ord(polyline_str[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1f:
                break
        lng += (~result >> 1) if (result & 1) != 0 else (result >> 1)
        
        coordinates.append((lat / 1e5, lng / 1e5))
    
    return coordinates

def fetch_transport_rest_routes():
    """
    Fetch routes from German DB Transport.rest API.
    
    Returns:
        List of route coordinates
    """
    print("Fetching routes from Transport.rest API...")
    try:
        # Get available lines
        lines_url = "https://v5.db.transport.rest/lines"
        res = requests.get(lines_url, timeout=30)
        res.raise_for_status()
        lines = res.json()
        
        routes = []
        max_lines = 50  # Limit to prevent too many API calls
        
        for i, line in enumerate(lines[:max_lines]):
            line_id = line.get("id")
            if not line_id:
                continue
                
            print(f"Processing line {i+1}/{min(len(lines), max_lines)}: {line_id}")
            
            try:
                # Get route for this line
                route_url = f"https://v5.db.transport.rest/lines/{quote(str(line_id))}/route"
                route_res = requests.get(route_url, timeout=10)
                
                if route_res.status_code != 200:
                    continue
                    
                route_data = route_res.json()
                
                # Extract coordinates from polyline or stops
                if "polyline" in route_data and route_data["polyline"]:
                    coords = decode_polyline(route_data["polyline"])
                    if len(coords) > 1:
                        routes.append(coords)
                elif "stops" in route_data:
                    # Extract coordinates from stops if no polyline
                    coords = []
                    for stop in route_data.get("stops", []):
                        if "location" in stop and "latitude" in stop["location"] and "longitude" in stop["location"]:
                            coords.append((stop["location"]["latitude"], stop["location"]["longitude"]))
                    if len(coords) > 1:
                        routes.append(coords)
                        
            except Exception as e:
                print(f"Error processing line {line_id}: {e}")
                continue
                
            # Small delay to be respectful to the API
            time.sleep(0.1)
        
        print(f"Successfully fetched {len(routes)} routes from Transport.rest")
        return routes
        
    except Exception as e:
        print(f"Transport.rest API error: {e}")
        return []

def fetch_osm_routes_via_overpass(bbox=None, route_types=None):
    """
    Fetch public transport routes from OpenStreetMap via Overpass API.
    Enhanced with route metadata extraction for better transport type detection.
    
    Args:
        bbox: Bounding box as (south, west, north, east) tuple
        route_types: List of route types to fetch (default: bus, train, tram)
        
    Returns:
        List of route coordinates with metadata
    """
    print("Fetching routes from OpenStreetMap Overpass API...")
    
    if route_types is None:
        route_types = ["bus", "train", "tram", "subway", "light_rail"]
    
    # Default to Germany/Central Europe if no bbox provided
    if bbox is None:
        bbox = (47.0, 5.0, 55.0, 15.0)  # Germany and surrounding areas
    
    route_filter = "|".join(route_types)
    
    overpass_query = f"""
    [out:json][timeout:60];
    (
      relation["route"~"^({route_filter})$"]["public_transport"="route"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
    );
    out geom;
    """
    
    try:
        overpass_url = "https://overpass-api.de/api/interpreter"
        response = requests.post(overpass_url, data=overpass_query, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        routes_with_metadata = []
        
        for element in data.get("elements", []):
            if element.get("type") == "relation":
                try:
                    # Extract route metadata
                    tags = element.get("tags", {})
                    route_type = tags.get("route", "unknown")
                    operator = tags.get("operator", "unknown")
                    route_name = tags.get("name", tags.get("ref", ""))
                    
                    # Extract coordinates from members
                    coords = []
                    stops = []
                    
                    for member in element.get("members", []):
                        if member.get("type") == "way" and "geometry" in member:
                            for node in member["geometry"]:
                                coords.append((node["lat"], node["lon"]))
                        elif member.get("type") == "node" and member.get("role") == "stop":
                            if "lat" in member and "lon" in member:
                                stops.append((member["lat"], member["lon"]))
                    
                    if len(coords) > 1:
                        # Create route metadata
                        route_id = f"osm_{element.get('id', 'unknown')}"
                        geometry_hash = hashlib.md5(str(coords[:10]).encode()).hexdigest()
                        
                        metadata = RouteMetadata(
                            route_id=route_id,
                            transport_type=route_type,
                            operator=operator,
                            route_name=route_name,
                            stops=stops,
                            geometry_hash=geometry_hash,
                            confidence_score=0.8  # OSM data is generally reliable
                        )
                        
                        routes_with_metadata.append({
                            "coordinates": coords,
                            "metadata": metadata
                        })
                        
                except Exception as e:
                    print(f"Error processing OSM route: {e}")
                    continue
        
        print(f"Successfully fetched {len(routes_with_metadata)} routes from OSM")
        return routes_with_metadata
        
    except Exception as e:
        print(f"OSM Overpass API error: {e}")
        return []

def fetch_transitland_routes(api_key=None, bbox=None):
    """
    Fetch routes from Transitland API.
    
    Args:
        api_key: Optional Transitland API key for higher rate limits
        bbox: Bounding box as (west, south, east, north) tuple
        
    Returns:
        List of route coordinates
    """
    print("Fetching routes from Transitland API...")
    
    if bbox is None:
        # Default to Berlin area
        bbox = (13.0, 52.3, 13.8, 52.7)
    
    try:
        base_url = "https://transit.land/api/v2/rest/routes"
        headers = {"User-Agent": "TravelTime-Backend/1.0"}
        
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        params = {
            "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
            "limit": 100,
            "include_geometry": "true"
        }
        
        res = requests.get(base_url, params=params, headers=headers, timeout=30)
        res.raise_for_status()
        data = res.json()
        
        routes = []
        
        for route in data.get("routes", []):
            try:
                geometry = route.get("geometry")
                if geometry and geometry.get("type") == "LineString":
                    coords = geometry.get("coordinates", [])
                    # Convert [lon, lat] to [lat, lon]
                    route_coords = [(coord[1], coord[0]) for coord in coords]
                    if len(route_coords) > 1:
                        routes.append(route_coords)
                        
            except Exception as e:
                print(f"Error processing Transitland route: {e}")
                continue
        
        print(f"Successfully fetched {len(routes)} routes from Transitland")
        return routes
        
    except Exception as e:
        print(f"Transitland API error: {e}")
        return []

def fetch_gtfs_routes_from_url(gtfs_url):
    """
    Fetch routes from a GTFS feed URL.
    
    Args:
        gtfs_url: URL to GTFS zip file
        
    Returns:
        List of route coordinates
    """
    print(f"Fetching GTFS data from {gtfs_url}")
    
    try:
        # Download GTFS zip file
        response = requests.get(gtfs_url, timeout=60)
        response.raise_for_status()
        
        routes = []
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as gtfs_zip:
            # Read shapes.txt for route geometries
            if "shapes.txt" in gtfs_zip.namelist():
                shapes_data = gtfs_zip.read("shapes.txt").decode('utf-8')
                shapes_lines = shapes_data.strip().split('\n')
                
                if len(shapes_lines) > 1:  # Has header
                    header = shapes_lines[0].split(',')
                    shape_id_idx = header.index('shape_id')
                    lat_idx = header.index('shape_pt_lat')
                    lon_idx = header.index('shape_pt_lon')
                    seq_idx = header.index('shape_pt_sequence')
                    
                    shapes_dict = {}
                    
                    for line in shapes_lines[1:]:
                        try:
                            fields = line.split(',')
                            shape_id = fields[shape_id_idx]
                            lat = float(fields[lat_idx])
                            lon = float(fields[lon_idx])
                            seq = int(fields[seq_idx])
                            
                            if shape_id not in shapes_dict:
                                shapes_dict[shape_id] = []
                            
                            shapes_dict[shape_id].append((seq, lat, lon))
                            
                        except (ValueError, IndexError):
                            continue
                    
                    # Sort coordinates by sequence and extract routes
                    for shape_id, points in shapes_dict.items():
                        points.sort(key=lambda x: x[0])  # Sort by sequence
                        coords = [(point[1], point[2]) for point in points]  # (lat, lon)
                        if len(coords) > 1:
                            routes.append(coords)
        
        print(f"Successfully extracted {len(routes)} routes from GTFS feed")
        return routes
        
    except Exception as e:
        print(f"GTFS fetch error: {e}")
        return []

def get_public_gtfs_feeds():
    """
    Get a list of public GTFS feed URLs.
    
    Returns:
        List of GTFS feed URLs
    """
    # Some example public GTFS feeds
    return [
        # Berlin VBB
        "https://www.vbb.de/media/download/2029",
        # San Francisco Bay Area
        "https://gtfs.sfmta.com/transitdata/google_transit.zip",
        # NYC MTA
        "http://web.mta.info/developers/data/nyct/subway/google_transit.zip",
        # London TfL (if available)
        # Add more feeds as needed
    ]

def cache_routes(routes):
    with open(CACHE_FILE, "w") as f:
        json.dump(routes, f)

def load_cached_routes():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return []

def get_all_routes(sources=None, bbox=None, max_routes=1000):
    """
    Fetch routes from multiple data sources and combine them.
    
    Args:
        sources: List of data sources to use (default: all available)
        bbox: Bounding box for geographic filtering
        max_routes: Maximum number of routes to return
        
    Returns:
        List of route coordinates
    """
    if sources is None:
        sources = ["osm", "transport_rest", "transitland"]
    
    print(f"Fetching routes from sources: {sources}")
    all_routes = []
    
    # OpenStreetMap via Overpass API
    if "osm" in sources:
        try:
            osm_routes = fetch_osm_routes_via_overpass(bbox=bbox)
            all_routes.extend(osm_routes)
            print(f"Added {len(osm_routes)} routes from OpenStreetMap")
        except Exception as e:
            print(f"Failed to fetch OSM routes: {e}")
    
    # German DB Transport.rest API
    if "transport_rest" in sources:
        try:
            db_routes = fetch_transport_rest_routes()
            all_routes.extend(db_routes)
            print(f"Added {len(db_routes)} routes from Transport.rest")
        except Exception as e:
            print(f"Failed to fetch Transport.rest routes: {e}")
    
    if "transitland" in sources:
        try:
            transitland_routes = fetch_transitland_routes(bbox=bbox)
            all_routes.extend(transitland_routes)
            print(f"Added {len(transitland_routes)} routes from Transitland")
        except Exception as e:
            print(f"Failed to fetch Transitland routes: {e}")
    
    if "gtfs" in sources:
        try:
            gtfs_feeds = get_public_gtfs_feeds()
            for feed_url in gtfs_feeds[:2]:  # Limit to first 2 
                try:
                    gtfs_routes = fetch_gtfs_routes_from_url(feed_url)
                    all_routes.extend(gtfs_routes)
                    print(f"Added {len(gtfs_routes)} routes from GTFS feed")
                except Exception as e:
                    print(f"Failed to fetch GTFS feed {feed_url}: {e}")
        except Exception as e:
            print(f"Failed to fetch GTFS routes: {e}")
    
    # Remove duplicates and filter by length
    unique_routes = []
    seen_routes = set()
    
    for route in all_routes:
        if len(route) < 2:  # Skip routes with less than 2 points
            continue
            
        # hash to detect duplicates
        route_hash = hash(tuple(tuple(coord) for coord in route[:10]))  # Use first 10 points for hash
        
        if route_hash not in seen_routes:
            seen_routes.add(route_hash)
            unique_routes.append(route)
            
        if len(unique_routes) >= max_routes:
            break
    
    print(f"Total unique routes collected: {len(unique_routes)}")
    
    # Cache the results
    cache_routes(unique_routes)
    
    return unique_routes

def update_route_cache(force_update=False):
    """
    Update the route cache with fresh data from all sources.
    
    Args:
        force_update: Force update even if cache exists
        
    Returns:
        Number of routes cached
    """
    if not force_update and os.path.exists(CACHE_FILE):
        print("Route cache already exists. Use force_update=True to refresh.")
        cached_routes = load_cached_routes()
        return len(cached_routes)
    
    print("Updating route cache...")
    
    # Fetch routes from all sources
    routes = get_all_routes()
    
    # Save metadata about the cache
    cache_metadata = {
        "routes": routes,
        "cache_created": time.time(),
        "total_routes": len(routes),
        "sources_used": ["osm", "transport_rest", "transitland"]
    }
    
    with open(CACHE_FILE, "w") as f:
        json.dump(cache_metadata, f)
    
    print(f"Route cache updated with {len(routes)} routes")
    return len(routes)

class RouteManager:
    """Manages route loading and caching."""
    
    def __init__(self):
        self._routes = None
        self._routes_lines = None
        self._spatial_index = {}
        self._loaded = False
        self._cache_file = CACHE_FILE
        
    def _load_routes(self):
        """Load routes from cache or APIs."""
        if self._loaded:
            return
            
        print("Loading routes...")
        
        if os.path.exists(self._cache_file):
            try:
                with open(self._cache_file, "r") as f:
                    cache_data = json.load(f)
                
                # Check if cache is stale (7 days)
                cache_age = time.time() - cache_data.get("cache_created", 0)
                if cache_age > 7 * 24 * 3600:
                    print("Cache is old, fetching new routes...")
                    self._routes = get_all_routes()
                    self._update_cache()
                else:
                    self._routes = cache_data.get("routes", [])
                    print(f"Loaded {len(self._routes)} routes from cache")
                    
            except Exception as e:
                print(f"Cache corrupted: {e}")
                self._routes = get_all_routes()
                self._update_cache()
        else:
            print("No cache, fetching routes...")
            self._routes = get_all_routes()
            self._update_cache()
        
        # Convert to LineString objects
        self._routes_lines = []
        for i, route in enumerate(self._routes):
            if len(route) > 1:
                try:
                    self._routes_lines.append(LineString(route))
                except Exception as e:
                    print(f"Route {i} invalid: {e}")
        
        # Build spatial index
        self._build_spatial_index()
        
        self._loaded = True
        print(f"Route loading complete: {len(self._routes_lines)} valid routes")
    
    def _update_cache(self):
        """Update the route cache file."""
        cache_data = {
            "routes": self._routes,
            "cache_created": time.time(),
            "total_routes": len(self._routes),
            "version": "2.0"
        }
        
        try:
            with open(self._cache_file, "w") as f:
                json.dump(cache_data, f)
            print(f"Cache updated with {len(self._routes)} routes")
        except Exception as e:
            print(f"Failed to update cache: {e}")
    
    def _build_spatial_index(self):
        """Build a spatial index for faster route lookups."""
        print("Building spatial index...")
        
        # Create a grid-based spatial index
        grid_size = 0.01  # ~1km grid cells
        
        for i, line in enumerate(self._routes_lines):
            try:
                bounds = line.bounds  # (minx, miny, maxx, maxy)
                
                # Calculate grid cells that this route intersects
                min_grid_x = int(bounds[0] / grid_size)
                max_grid_x = int(bounds[2] / grid_size)
                min_grid_y = int(bounds[1] / grid_size)
                max_grid_y = int(bounds[3] / grid_size)
                
                # Add route to all intersecting grid cells
                for gx in range(min_grid_x, max_grid_x + 1):
                    for gy in range(min_grid_y, max_grid_y + 1):
                        grid_key = (gx, gy)
                        if grid_key not in self._spatial_index:
                            self._spatial_index[grid_key] = []
                        self._spatial_index[grid_key].append(i)
                        
            except Exception as e:
                print(f"Error indexing route {i}: {e}")
                continue
        
        print(f"Spatial index built with {len(self._spatial_index)} grid cells")
    
    def get_nearby_routes_optimized(self, lat, lon, radius_meters=1000):
        """
        Get nearby routes using spatial index for better performance.
        """
        self._load_routes()
        
        if not self._routes_lines:
            return []
        
        # Convert radius to degrees (approximate)
        radius_degrees = radius_meters / DEGREES_TO_METERS
        grid_size = 0.01
        
        # Calculate which grid cells to check
        grid_range = max(1, int(radius_degrees / grid_size) + 1)
        center_grid_x = int(lat / grid_size)
        center_grid_y = int(lon / grid_size)
        
        candidate_routes = set()
        
        # Check nearby grid cells
        for gx in range(center_grid_x - grid_range, center_grid_x + grid_range + 1):
            for gy in range(center_grid_y - grid_range, center_grid_y + grid_range + 1):
                grid_key = (gx, gy)
                if grid_key in self._spatial_index:
                    candidate_routes.update(self._spatial_index[grid_key])
        
        # Filter candidates by actual distance
        user_point = Point(lat, lon)
        user_area = user_point.buffer(radius_degrees)
        
        nearby_routes = []
        for route_idx in candidate_routes:
            try:
                if route_idx < len(self._routes_lines):
                    route = self._routes_lines[route_idx]
                    if route.intersects(user_area):
                        nearby_routes.append(route)
            except Exception as e:
                print(f"Error checking route {route_idx}: {e}")
                continue
        
        return nearby_routes
    
    def get_routes_lines(self):
        """Get all route lines (loads routes if not already loaded)."""
        self._load_routes()
        return self._routes_lines
    
    def get_routes_count(self):
        """Get total number of routes."""
        self._load_routes()
        return len(self._routes_lines)
    
    def refresh_cache(self):
        """Force refresh of route cache."""
        print("Forcing route cache refresh...")
        self._routes = get_all_routes()
        self._update_cache()
        self._routes_lines = None
        self._spatial_index = {}
        self._loaded = False
        self._load_routes()

# Global route manager instance
route_manager = RouteManager()

# Legacy compatibility functions
def get_routes():
    """Get raw route data for backwards compatibility."""
    route_manager._load_routes()
    return route_manager._routes or []

def get_routes_lines():
    """Get route LineString objects for backwards compatibility."""
    return route_manager.get_routes_lines()

DEGREES_TO_METERS = 111139  
ROUTE_WIDTH_METERS = 20     
RESAMPLE_EVERY_METERS = 10  

def interpolate_linestring(line: LineString, step_meters: float):
    total_length = line.length
    step_fraction = step_meters / (DEGREES_TO_METERS * 1.0)
    num_points = math.ceil(total_length / step_fraction)

    points = [line.interpolate(i / num_points, normalized=True) for i in range(num_points + 1)]
    return LineString(points)

def buffer_routes(routes_lines, buffer_meters: float = ROUTE_WIDTH_METERS):
    buffer_deg = buffer_meters / DEGREES_TO_METERS
    return [interpolate_linestring(route, RESAMPLE_EVERY_METERS).buffer(buffer_deg) for route in routes_lines]

def is_user_on_any_buffered_route(user_lat, user_lon, buffered_routes):
    user_point = Point(user_lat, user_lon)
    return any(buffer.contains(user_point) for buffer in buffered_routes)

def get_nearby_routes(user_lat, user_lon, routes_lines=None, radius_meters=1000):
    """
    Get routes near a user location.
    Now uses optimized spatial indexing for better performance.
    """
    return route_manager.get_nearby_routes_optimized(user_lat, user_lon, radius_meters)

def buffer_nearby_routes(user_lat, user_lon, routes_lines=None):
    nearby_routes = get_nearby_routes(user_lat, user_lon, routes_lines, radius_meters=1000)
    print(f"Found {len(nearby_routes)} nearby routes")

    buffered = []
    for route in nearby_routes:
        try:
            interpolated = interpolate_linestring(route, RESAMPLE_EVERY_METERS)
            buffer_radius = ROUTE_WIDTH_METERS / DEGREES_TO_METERS
            buffered.append(interpolated.buffer(buffer_radius))
        except Exception as e:
            print(f"Error buffering route: {e}")
            continue
    return buffered

def is_user_on_any_nearby_route(user_lat, user_lon, routes_lines=None):
    try:
        buffered_routes = buffer_nearby_routes(user_lat, user_lon, routes_lines)
        user_point = Point(user_lat, user_lon)
        return any(buf.contains(user_point) for buf in buffered_routes)
    except Exception as e:
        print(f"Error checking if user is on route: {e}")
        return False

def gpsinput(user_id, lat, lon, timestamp=None):
    """
    Enhanced GPS input processing that tracks travel sessions and calculates duration.
    
    This function determines if a user is on public transportation by checking their
    GPS coordinates against known transit routes, and manages travel sessions with
    proper state tracking.
    
    Args:
        user_id: User identifier (string or int)
        lat: Latitude coordinate (-90 to 90)
        lon: Longitude coordinate (-180 to 180)
        timestamp: Optional ISO timestamp string or datetime object
    
    Returns:
        dict: Travel session information containing:
            - on_transport: Boolean indicating if user is on public transport
            - session_type: "new", "continuing", "ended", "invalid", or "none"
            - duration: Duration in seconds of current/completed session
            - distance: Distance traveled in kilometers
            - transport_type: Detected transport type ("bus", "train", "tram", etc.)
            - travel_id: Database ID of the travel session
    """
    from misc.db import get_session
    from misc.models import TravelHistory, User
    from sqlmodel import select
    from datetime import datetime, timedelta
    import time
    
    # Input validation
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid user_id: {user_id}. Must be convertible to integer.")
    
    if not (-90 <= lat <= 90):
        raise ValueError(f"Invalid latitude: {lat}. Must be between -90 and 90.")
    
    if not (-180 <= lon <= 180):
        raise ValueError(f"Invalid longitude: {lon}. Must be between -180 and 180.")
    
    # Handle timestamp conversion
    if timestamp is None:
        timestamp = datetime.utcnow()
    elif isinstance(timestamp, str):
        try:
            # Handle various ISO format variations
            timestamp = timestamp.replace('Z', '+00:00')
            timestamp = datetime.fromisoformat(timestamp)
        except ValueError as e:
            print(f"Warning: Invalid timestamp format '{timestamp}', using current time. Error: {e}")
            timestamp = datetime.utcnow()
    elif not isinstance(timestamp, datetime):
        print(f"Warning: Unexpected timestamp type {type(timestamp)}, using current time.")
        timestamp = datetime.utcnow()
    
    # Check if user is on any transportation route
    try:
        is_on_route = is_user_on_any_nearby_route(lat, lon)
    except Exception as e:
        print(f"Error checking route proximity: {e}")
        is_on_route = False
    
    try:
        with get_session() as session:
            # Verify user exists
            user_statement = select(User).where(User.id == user_id_int)
            user = session.exec(user_statement).first()
            if not user:
                raise ValueError(f"User with ID {user_id} not found.")
            
            # Get the most recent travel history for this user
            statement = select(TravelHistory).where(
                TravelHistory.user_id == user_id_int
            ).order_by(TravelHistory.timestamp.desc()).limit(1)
            
            last_travel = session.exec(statement).first()
            
            if is_on_route:
                # User is currently on a transportation route
                session_timeout_minutes = 10
                
                if (last_travel and 
                    last_travel.timestamp > (timestamp - timedelta(minutes=session_timeout_minutes))):
                    
     
                    if last_travel.listLatitude is None:
                        last_travel.listLatitude = [last_travel.startLatitude]
                    if last_travel.listLongitude is None:
                        last_travel.listLongitude = [last_travel.startLongitude]
                    
                    last_travel.listLatitude.append(lat)
                    last_travel.listLongitude.append(lon)
                    
                    duration_seconds = (timestamp - last_travel.timestamp).total_seconds()
                    last_travel.duration = duration_seconds
                    
                    # Calculate total distance traveled using all coordinates
                    if len(last_travel.listLatitude) > 1:
                        try:
                            distance = calculate_total_distance(
                                last_travel.listLatitude, 
                                last_travel.listLongitude
                            )
                            last_travel.distance = distance
                        except Exception as e:
                            print(f"Error calculating distance: {e}")
                            last_travel.distance = 0.0
                    
                    # Update the session in database
                    session.add(last_travel)
                    session.commit()
                    
                    return {
                        "on_transport": True,
                        "session_type": "continuing",
                        "duration": duration_seconds,
                        "distance": last_travel.distance,
                        "transport_type": detect_transport_type(lat, lon),
                        "travel_id": last_travel.id
                    }
                else:
                    # Start new travel session
                    try:
                        new_travel = TravelHistory(
                            user_id=user_id_int,
                            timestamp=timestamp,
                            startLatitude=lat,
                            startLongitude=lon,
                            listLatitude=[lat],
                            listLongitude=[lon],
                            distance=0.0,
                            duration=0.0
                        )
                        session.add(new_travel)
                        session.commit()
                        session.refresh(new_travel)
                        
                        return {
                            "on_transport": True,
                            "session_type": "new",
                            "duration": 0.0,
                            "distance": 0.0,
                            "transport_type": detect_transport_type(lat, lon),
                            "travel_id": new_travel.id
                        }
                    except Exception as e:
                        print(f"Error creating new travel session: {e}")
                        return {
                            "on_transport": False,
                            "session_type": "error",
                            "duration": 0.0,
                            "distance": 0.0,
                            "transport_type": None,
                            "travel_id": None
                        }
            else:
                # User is not on a transportation route
                session_end_timeout_minutes = 15
                minimum_valid_duration_seconds = 120  # 2 minutes
                
                if (last_travel and 
                    last_travel.timestamp > (timestamp - timedelta(minutes=session_end_timeout_minutes))):
                    
                    # Recently was on transport, consider this the end of travel session
                    final_duration = (timestamp - last_travel.timestamp).total_seconds()
                    
                    if final_duration > minimum_valid_duration_seconds:
                        # Valid travel session completed
                        last_travel.duration = final_duration
                        session.add(last_travel)
                        session.commit()
                        
                        return {
                            "on_transport": False,
                            "session_type": "ended",
                            "duration": final_duration,
                            "distance": last_travel.distance,
                            "transport_type": detect_transport_type(lat, lon),
                            "travel_id": last_travel.id
                        }
                    else:
                        # Session too short to be valid transport, remove it
                        try:
                            session.delete(last_travel)
                            session.commit()
                        except Exception as e:
                            print(f"Error deleting invalid travel session: {e}")
                        
                        return {
                            "on_transport": False,
                            "session_type": "invalid",
                            "duration": 0.0,
                            "distance": 0.0,
                            "transport_type": None,
                            "travel_id": None
                        }
                
                # No active or recent travel session
                return {
                    "on_transport": False,
                    "session_type": "none",
                    "duration": 0.0,
                    "distance": 0.0,
                    "transport_type": None,
                    "travel_id": None
                }
                
    except Exception as e:
        print(f"Database error in gpsinput: {e}")
        return {
            "on_transport": False,
            "session_type": "error",
            "duration": 0.0,
            "distance": 0.0,
            "transport_type": None,
            "travel_id": None
        }


def calculate_total_distance(latitudes, longitudes):
    """Calculate total distance traveled using Haversine formula"""
    import math
    
    if len(latitudes) < 2:
        return 0.0
    
    total_distance = 0.0
    
    for i in range(1, len(latitudes)):
        lat1, lon1 = math.radians(latitudes[i-1]), math.radians(longitudes[i-1])
        lat2, lon2 = math.radians(latitudes[i]), math.radians(longitudes[i])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        distance = r * c
        total_distance += distance
    
    return total_distance

def detect_transport_type(lat, lon, speed_kmh=None, travel_history=None):
    """
    Enhanced transport type detection using multiple data sources and machine learning patterns.
    
    Args:
        lat: Latitude
        lon: Longitude  
        speed_kmh: Optional speed in km/h
        travel_history: Optional list of recent travel points
    
    Returns:
        Tuple of (transport_type, confidence_score)
    """
    try:
        # Get nearby routes with metadata
        nearby_routes = get_nearby_routes(lat, lon, radius_meters=100)
        
        if not nearby_routes:
            return "unknown", 0.0
        
        # Use analytics system for prediction
        stop_pattern = None
        if travel_history and len(travel_history) > 2:
            stop_pattern = [(point.get('lat', 0), point.get('lon', 0)) for point in travel_history[-10:]]
        
        transport_type, confidence = route_analytics.predict_transport_type(
            lat, lon, speed_kmh, stop_pattern
        )
        
        # Update usage analytics
        route_id = f"route_{hash((lat, lon))}"
        route_analytics.update_route_usage(route_id, transport_type)
        
        # Learn from this interaction if we have speed data
        if speed_kmh is not None and travel_history and len(travel_history) > 5:
            recent_speeds = [point.get('speed', 0) for point in travel_history[-5:] if point.get('speed', 0) > 0]
            if recent_speeds:
                route_analytics.learn_transport_pattern(
                    transport_type, 
                    recent_speeds, 
                    len(travel_history) / 10.0,  # Simplified stop frequency
                    f"route_{hash((lat, lon))}"
                )
        
        return transport_type, confidence
        
    except Exception as e:
        print(f"Error in enhanced transport type detection: {e}")
        return "unknown", 0.0 


def get_user_travel_stats(user_id, timeframe="daily"):
    """Get user travel statistics for different timeframes"""
    from misc.db import get_session
    from misc.models import TravelHistory
    from sqlmodel import select
    from datetime import datetime, timedelta
    
    with get_session() as session:
        now = datetime.utcnow()
        
        if timeframe == "daily":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "weekly":
            start_time = now - timedelta(days=7)
        elif timeframe == "monthly":
            start_time = now - timedelta(days=30)
        else:
            start_time = datetime.min
        
        statement = select(TravelHistory).where(
            TravelHistory.user_id == int(user_id),
            TravelHistory.timestamp >= start_time,
            TravelHistory.duration > 120  # Only count trips longer than 2 minutes
        )
        
        travels = session.exec(statement).all()
        
        total_duration = sum(travel.duration for travel in travels)
        total_distance = sum(travel.distance for travel in travels)
        trip_count = len(travels)
        
        return {
            "timeframe": timeframe,
            "total_duration_minutes": total_duration / 60,
            "total_distance_km": total_distance,
            "trip_count": trip_count,
            "average_trip_duration": (total_duration / trip_count / 60) if trip_count > 0 else 0,
            "average_trip_distance": (total_distance / trip_count) if trip_count > 0 else 0
        }

class RouteAnalytics:
    """Track route usage and learn transport patterns."""
    
    def __init__(self):
        self.analytics_cache = {}
        self.transport_patterns = {}
        self.route_usage_stats = defaultdict(int)
        self.operator_stats = defaultdict(lambda: defaultdict(int))
        self.popular_routes = []
        self._load_analytics_cache()
        self._load_transport_patterns()
    
    def _load_analytics_cache(self):
        """Load cached analytics data."""
        try:
            if os.path.exists(ANALYTICS_CACHE_FILE):
                with open(ANALYTICS_CACHE_FILE, 'rb') as f:
                    data = pickle.load(f)
                    self.analytics_cache = data.get('analytics_cache', {})
                    self.route_usage_stats = data.get('route_usage_stats', defaultdict(int))
                    self.operator_stats = data.get('operator_stats', defaultdict(lambda: defaultdict(int)))
                    self.popular_routes = data.get('popular_routes', [])
                    print(f"Loaded {len(self.analytics_cache)} analytics entries")
        except Exception as e:
            print(f"Analytics cache load failed: {e}")
    
    def _save_analytics_cache(self):
        """Save analytics to file."""
        try:
            data = {
                'analytics_cache': self.analytics_cache,
                'route_usage_stats': dict(self.route_usage_stats),
                'operator_stats': dict(self.operator_stats),
                'popular_routes': self.popular_routes
            }
            with open(ANALYTICS_CACHE_FILE, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Error saving analytics cache: {e}")
    
    def _load_transport_patterns(self):
        """Load transport type patterns from SQLite database."""
        try:
            if os.path.exists(TRANSPORT_PATTERNS_FILE):
                conn = sqlite3.connect(TRANSPORT_PATTERNS_FILE)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT transport_type, speed_profile, stop_frequency, 
                           route_geometry, confidence, sample_count
                    FROM transport_patterns
                ''')
                
                for row in cursor.fetchall():
                    transport_type, speed_profile, stop_frequency, route_geometry, confidence, sample_count = row
                    self.transport_patterns[transport_type] = TransportTypePattern(
                        speed_profile=pickle.loads(speed_profile),
                        stop_frequency=stop_frequency,
                        route_geometry=route_geometry,
                        confidence=confidence,
                        sample_count=sample_count
                    )
                
                conn.close()
                print(f"Loaded {len(self.transport_patterns)} transport patterns")
        except Exception as e:
            print(f"Error loading transport patterns: {e}")
            self._create_transport_patterns_db()
    
    def _create_transport_patterns_db(self):
        """Create the transport patterns database."""
        try:
            conn = sqlite3.connect(TRANSPORT_PATTERNS_FILE)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transport_patterns (
                    transport_type TEXT PRIMARY KEY,
                    speed_profile BLOB,
                    stop_frequency REAL,
                    route_geometry TEXT,
                    confidence REAL,
                    sample_count INTEGER
                )
            ''')
            conn.commit()
            conn.close()
            print("Created transport patterns database")
        except Exception as e:
            print(f"Error creating transport patterns database: {e}")
    
    def update_route_usage(self, route_id: str, transport_type: str = None, operator: str = None):
        """Update route usage statistics."""
        self.route_usage_stats[route_id] += 1
        
        if transport_type:
            self.operator_stats[operator or 'unknown'][transport_type] += 1
        
        # Update popular routes list
        self._update_popular_routes()
        
        # Save periodically
        if sum(self.route_usage_stats.values()) % 100 == 0:
            self._save_analytics_cache()
    
    def _update_popular_routes(self):
        """Update the list of popular routes."""
        sorted_routes = sorted(self.route_usage_stats.items(), key=lambda x: x[1], reverse=True)
        self.popular_routes = sorted_routes[:50]  # Keep top 50
    
    def get_route_analytics(self, route_id: str) -> Dict[str, Any]:
        """Get analytics for a specific route."""
        if route_id not in self.analytics_cache:
            return {"usage_count": 0, "last_used": None, "confidence": 0.0}
        
        return self.analytics_cache[route_id]
    
    def get_popular_routes(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most popular routes."""
        return self.popular_routes[:limit]
    
    def get_operator_stats(self) -> Dict[str, Dict[str, int]]:
        """Get operator statistics."""
        return dict(self.operator_stats)
    
    def analyze_transport_patterns(self, user_travel_data: List[Dict]) -> Dict[str, Any]:
        """Analyze transport patterns from user travel data."""
        if not user_travel_data:
            return {}
        
        # Group by transport type
        transport_data = defaultdict(list)
        for travel in user_travel_data:
            transport_type = travel.get('transport_type', 'unknown')
            transport_data[transport_type].append(travel)
        
        analysis = {}
        for transport_type, travels in transport_data.items():
            if len(travels) > 1:
                speeds = [t.get('avg_speed', 0) for t in travels if t.get('avg_speed', 0) > 0]
                distances = [t.get('distance', 0) for t in travels if t.get('distance', 0) > 0]
                durations = [t.get('duration', 0) for t in travels if t.get('duration', 0) > 0]
                
                if speeds and distances and durations:
                    analysis[transport_type] = {
                        'avg_speed': statistics.mean(speeds),
                        'avg_distance': statistics.mean(distances),
                        'avg_duration': statistics.mean(durations),
                        'trip_count': len(travels),
                        'speed_variance': statistics.variance(speeds) if len(speeds) > 1 else 0,
                        'pattern_confidence': min(len(travels) / 10.0, 1.0)  # Confidence based on sample size
                    }
        
        return analysis
    
    def predict_transport_type(self, lat: float, lon: float, speed_kmh: float = None, 
                             stop_pattern: List[Tuple[float, float]] = None) -> Tuple[str, float]:
        """
        Predict transport type based on location, speed, and stop patterns.
        
        Returns:
            Tuple of (transport_type, confidence_score)
        """
        predictions = []
        
        # Speed-based prediction
        if speed_kmh is not None:
            if speed_kmh < 15:
                predictions.append(('bus', 0.7))
            elif speed_kmh < 35:
                predictions.append(('tram', 0.6))
            elif speed_kmh < 80:
                predictions.append(('train', 0.8))
            else:
                predictions.append(('train', 0.9))
        
        # Pattern-based prediction using learned patterns
        if stop_pattern and len(stop_pattern) > 2:
            # Calculate stop frequency
            total_distance = 0
            for i in range(1, len(stop_pattern)):
                lat1, lon1 = stop_pattern[i-1]
                lat2, lon2 = stop_pattern[i]
                distance = calculate_distance(lat1, lon1, lat2, lon2)
                total_distance += distance
            
            if total_distance > 0:
                avg_stop_distance = total_distance / (len(stop_pattern) - 1)
                
                if avg_stop_distance < 0.5:  # Very frequent stops
                    predictions.append(('bus', 0.8))
                elif avg_stop_distance < 1.5:  # Moderate stops
                    predictions.append(('tram', 0.7))
                else:  # Infrequent stops
                    predictions.append(('train', 0.8))
        
        # Use learned patterns for additional prediction
        for transport_type, pattern in self.transport_patterns.items():
            if pattern.confidence > 0.5:
                # Simple pattern matching based on confidence
                predictions.append((transport_type, pattern.confidence * 0.5))
        
        # Combine predictions
        if predictions:
            # Weight by confidence and return most likely
            weighted_predictions = defaultdict(float)
            for transport_type, confidence in predictions:
                weighted_predictions[transport_type] += confidence
            
            best_prediction = max(weighted_predictions.items(), key=lambda x: x[1])
            return best_prediction[0], min(best_prediction[1], 1.0)
        
        return 'unknown', 0.0
    
    def learn_transport_pattern(self, transport_type: str, speed_data: List[float], 
                               stop_frequency: float, route_geometry: str):
        """Learn transport patterns from real usage data."""
        if transport_type not in self.transport_patterns:
            self.transport_patterns[transport_type] = TransportTypePattern()
        
        pattern = self.transport_patterns[transport_type]
        
        # Update speed profile
        pattern.speed_profile.extend(speed_data)
        if len(pattern.speed_profile) > 1000:  # Limit size
            pattern.speed_profile = pattern.speed_profile[-1000:]
        
        # Update stop frequency (exponential moving average)
        alpha = 0.1
        pattern.stop_frequency = alpha * stop_frequency + (1 - alpha) * pattern.stop_frequency
        
        # Update sample count and confidence
        pattern.sample_count += 1
        pattern.confidence = min(pattern.sample_count / 50.0, 1.0)
        
        # Update route geometry pattern
        pattern.route_geometry = route_geometry
        
        # Save to database
        self._save_transport_pattern(transport_type, pattern)
    
    def _save_transport_pattern(self, transport_type: str, pattern: TransportTypePattern):
        """Save transport pattern to database."""
        try:
            conn = sqlite3.connect(TRANSPORT_PATTERNS_FILE)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO transport_patterns
                (transport_type, speed_profile, stop_frequency, route_geometry, confidence, sample_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                transport_type,
                pickle.dumps(pattern.speed_profile),
                pattern.stop_frequency,
                pattern.route_geometry,
                pattern.confidence,
                pattern.sample_count
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving transport pattern: {e}")

# Global analytics instance
route_analytics = RouteAnalytics()

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula."""
    import math
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Earth's radius in kilometers
    
    return r * c

def gpsinput(user, lat, lon):
    return is_user_on_any_nearby_route(lat, lon)

def get_user_points(user_id):
    """Get user's current points from the database"""
    from misc.db import get_session
    from misc.models import User
    from sqlmodel import select
    
    with get_session() as session:
        user = session.exec(select(User).where(User.id == int(user_id))).first()
        if user:
            return user.points
        return 0


