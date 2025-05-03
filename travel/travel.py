# travel.py

from typing import List, Dict, Optional
from geopy.distance import geodesic
import httpx
import time
import math

TRANSIT_API_URL = "https://transit.land/api/v2/rest/vehicles"
TRANSIT_API_KEY = "your_api_key_here"
PROXIMITY_THRESHOLD_METERS = 100

user_travel_logs: Dict[str, List[Dict]] = {}
user_active_trips: Dict[str, Dict] = {}
user_points: Dict[str, int] = {}

async def fetch_live_transit_data() -> List[Dict]:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                TRANSIT_API_URL,
                params={"api_key": TRANSIT_API_KEY}
            )
            response.raise_for_status()
            return response.json().get("vehicles", [])
        except Exception as e:
            print(f"Transit API error: {e}")
            return []

async def check_if_on_transit(user_id: str, latitude: float, longitude: float, timestamp: Optional[float] = None):
    user_loc = (latitude, longitude)
    timestamp = timestamp or time.time()
    vehicles = await fetch_live_transit_data()

    is_on_transit = False
    matched_vehicle_id = None
    closest_distance = float("inf")

    for vehicle in vehicles:
        coords = vehicle.get("geometry", {}).get("coordinates", [])
        if len(coords) != 2:
            continue

        vehicle_loc = (coords[1], coords[0])
        distance = geodesic(user_loc, vehicle_loc).meters

        if distance < PROXIMITY_THRESHOLD_METERS and distance < closest_distance:
            is_on_transit = True
            matched_vehicle_id = vehicle.get("onestop_id")
            closest_distance = distance

    if is_on_transit:
        # Start or continue tracking
        active = user_active_trips.get(user_id)
        if not active:
            user_active_trips[user_id] = {
                "start_time": timestamp,
                "vehicle_id": matched_vehicle_id
            }
        elif active["vehicle_id"] != matched_vehicle_id:
            # Switched vehicle → treat as new trip
            await end_trip(user_id, timestamp)
            user_active_trips[user_id] = {
                "start_time": timestamp,
                "vehicle_id": matched_vehicle_id
            }

        return {
            "status": "on_transit",
            "vehicle_id": matched_vehicle_id,
            "distance_to_vehicle_m": round(closest_distance, 2)
        }

    else:
        # No longer on transit → end trip if needed
        if user_id in user_active_trips:
            await end_trip(user_id, timestamp)
        return {"status": "not_on_transit"}

async def end_trip(user_id: str, end_time: float):
    trip = user_active_trips.pop(user_id, None)
    if not trip:
        return

    duration_sec = end_time - trip["start_time"]
    minutes = max(1, math.floor(duration_sec / 60))
    user_points[user_id] = user_points.get(user_id, 0) + minutes

    log = user_travel_logs.setdefault(user_id, [])
    log.append({
        "vehicle_id": trip["vehicle_id"],
        "start_time": trip["start_time"],
        "end_time": end_time,
        "minutes": minutes,
        "points_awarded": minutes
    })

def get_user_log(user_id: str) -> List[Dict]:
    return user_travel_logs.get(user_id, [])

def get_user_points(user_id: str) -> int:
    return user_points.get(user_id, 0)
