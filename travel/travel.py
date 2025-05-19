import requests
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
import threading
import time
from functools import lru_cache

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

class JourneyTracker:
    def __init__(self, radius=10):
        self.radius = radius
        self.user_states = {}
        self.lock = threading.Lock()

    @staticmethod
    @lru_cache(maxsize=128)
    def _cached_overpass_query(lat, lon, radius):
        q = f"""
        [out:json];
        (
          relation["type"="route"](around:{radius},{lat},{lon});
        );
        out geom tags;
        """
        r = requests.post(OVERPASS_URL, data={"data": q})
        r.raise_for_status()
        data = r.json()
        routes = []
        for rel in data.get("elements", []):
            geom = rel.get("members", [])
            lines = []
            for m in geom:
                if m["type"] == "way" and "geometry" in m:
                    coords = [(pt["lon"], pt["lat"]) for pt in m["geometry"]]
                    lines.append(LineString(coords))
            if not lines:
                continue
            merged = unary_union(lines)
            name = rel["tags"].get("name", rel["tags"].get("ref", "unknown"))
            routes.append({
                "id": rel["id"],
                "name": name,
                "geometry": merged
            })
        return routes

    def _overpass_query(self, lat, lon):
        # Use cached version
        return self._cached_overpass_query(lat, lon, self.radius)

    @staticmethod
    @lru_cache(maxsize=256)
    def _compute_route_area_cached(wkb):
        poly: Polygon = LineString.from_wkb(wkb).buffer(1.0)
        return poly.area

    def _compute_route_area(self, geometry):
        # Use WKB as cache key
        return self._compute_route_area_cached(geometry.wkb)

    def process_ping(self, user_id: str, lat: float, lon: float, timestamp: float):
        pt = Point(lon, lat)
        with self.lock:
            state = self.user_states.get(user_id, {"state": "off_route"})
            if state["state"] == "off_route":
                routes = self._overpass_query(lat, lon)
                if not routes:
                    return None
                best = min(routes, key=lambda r: r["geometry"].distance(pt))
                area = self._compute_route_area(best["geometry"])
                state = {
                    "state": "on_route",
                    "route": {**best, "area_sqm": area},
                    "pings": [(lat, lon, timestamp)],
                    "start_time": timestamp,
                }
                self.user_states[user_id] = state
                return None
            else:
                geom = state["route"]["geometry"]
                dist = geom.distance(pt)
                if dist <= self.radius + 0.5:
                    state["pings"].append((lat, lon, timestamp))
                    return None
                else:
                    journey = {
                        "user_id": user_id,
                        "route_id": state["route"]["id"],
                        "route_name": state["route"]["name"],
                        "route_area_sqm": state["route"]["area_sqm"],
                        "start_time": state["start_time"],
                        "end_time": state["pings"][-1][2],
                        "duration_s": state["pings"][-1][2] - state["start_time"],
                        "pings": state["pings"],
                    }
                    self.user_states[user_id] = {"state": "off_route"}
                    return journey

# Create a single JourneyTracker instance
_jt_instance = JourneyTracker(radius=10)

def gpsinput(user, lat, lon):
    ts = time.time()
    return _jt_instance.process_ping(user, lat, lon, ts)
