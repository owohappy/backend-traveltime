import requests
from shapely.geometry import Point, LineString
import time
import requests
import json
import os
import math 

CACHE_FILE = "cached_routes.json"

def fetch_transport_rest_routes():
    try:
        res = requests.get("https://v5.db.transport.rest/lines")
        res.raise_for_status()
        lines = res.json()
        routes = []

        for line in lines:
            line_id = line.get("id")
            if not line_id:
                continue
            route_res = requests.get(f"https://v5.db.transport.rest/lines/{line_id}/route")
            if route_res.status_code != 200:
                continue
            route_data = route_res.json()
            if "polyline" in route_data:
                coords = decode_polyline(route_data["polyline"])
                routes.append(coords)
        return routes
    except Exception as e:
        print(f"Error fetching from transport.rest: {e}")
        return []

def fetch_osm_routes_via_overpass():
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = """
    [out:json];
    (
      relation["type"="route"]["route"~"bus|train|tram"](area:3600062421);
    );
    out geom;
    """
    try:
        res = requests.post(overpass_url, data={"data": overpass_query})
        res.raise_for_status()
        data = res.json()
        routes = []
        for element in data.get("elements", []):
            if "geometry" in element:
                coords = [(p["lat"], p["lon"]) for p in element["geometry"]]
                if len(coords) > 1:
                    routes.append(coords)
        return routes
    except Exception as e:
        print(f"Error fetching from Overpass API: {e}")
        return []

def decode_polyline(polyline_str):
    # Placeholder: assumes Google's encoded polyline format
    # Real decoding logic needed if using encoded polylines
<<<<<<< HEAD
    # Using parameter to avoid unused variable warning
    if polyline_str:
        pass
=======
>>>>>>> 9ad7059 (Implement transport route fetching and caching functionality; add unit tests for route-related functions)
    return []

def cache_routes(routes):
    with open(CACHE_FILE, "w") as f:
        json.dump(routes, f)

def load_cached_routes():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return []

def get_all_routes():
    print("Fetching routes from APIs...")
    routes = []
    routes += fetch_transport_rest_routes()
    routes += fetch_osm_routes_via_overpass()
    print(f"Fetched {len(routes)} routes.")
    cache_routes(routes)
    return routes

# Run once to cache routes locally
routes = get_all_routes() if not os.path.exists(CACHE_FILE) else load_cached_routes()
routes_lines = [LineString(r) for r in routes if len(r) > 1]

routes_lines[:2]  # Show a sample of the cached LineStrings



DEGREES_TO_METERS = 111139  
ROUTE_WIDTH_METERS = 20     
RESAMPLE_EVERY_METERS = 10  

def interpolate_linestring(line: LineString, step_meters: float):
    total_length = line.length
    step_fraction = step_meters / (DEGREES_TO_METERS * 1.0)  # convert to degrees length
    num_points = math.ceil(total_length / step_fraction)

    points = [line.interpolate(i / num_points, normalized=True) for i in range(num_points + 1)]
    return LineString(points)

def buffer_routes(routes_lines, buffer_meters: float = ROUTE_WIDTH_METERS):
    buffer_deg = buffer_meters / DEGREES_TO_METERS
    return [interpolate_linestring(route, RESAMPLE_EVERY_METERS).buffer(buffer_deg) for route in routes_lines]

def is_user_on_any_buffered_route(user_lat, user_lon, buffered_routes):
    user_point = Point(user_lat, user_lon)
    return any(buffer.contains(user_point) for buffer in buffered_routes)


def get_nearby_routes(user_lat, user_lon, routes_lines, radius_meters=1000):
    radius_degrees = radius_meters / DEGREES_TO_METERS
    user_point = Point(user_lat, user_lon)
    user_area = user_point.buffer(radius_degrees)

    return [route for route in routes_lines if route.intersects(user_area)]

def buffer_nearby_routes(user_lat, user_lon, routes_lines):
    nearby_routes = get_nearby_routes(user_lat, user_lon, routes_lines)
    print(f"Found {len(nearby_routes)} nearby routes within 1 km")

    buffered = []
    for route in nearby_routes:
        interpolated = interpolate_linestring(route, RESAMPLE_EVERY_METERS)
        buffer_radius = ROUTE_WIDTH_METERS / DEGREES_TO_METERS
        buffered.append(interpolated.buffer(buffer_radius))
    return buffered


def is_user_on_any_nearby_route(user_lat, user_lon, routes_lines):
    buffered_routes = buffer_nearby_routes(user_lat, user_lon, routes_lines)
    user_point = Point(user_lat, user_lon)
    return any(buf.contains(user_point) for buf in buffered_routes)
<<<<<<< HEAD
def gpsinput(user, lat, lon):
    # Parameters and variables used in logging or future implementation
    _ = user  # Acknowledge unused parameter
    _ = time.time()  # Timestamp for potential logging
    _ = Point(lat, lon)  # User point saved for reference
    
=======



def gpsinput(user, lat, lon):
    ts = time.time()
    user_point = Point(lat, lon)
>>>>>>> 9ad7059 (Implement transport route fetching and caching functionality; add unit tests for route-related functions)
    data = is_user_on_any_nearby_route(lat, lon, routes_lines)
    return data

