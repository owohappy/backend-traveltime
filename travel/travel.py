import requests
from shapely.geometry import Point, LineString, Polygon, mapping
from shapely.ops import unary_union
import threading
import time

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

class JourneyTracker:
    def __init__(self, radius=10):
        """
        radius: search radius in meters for detecting nearby routes
        """
        self.radius = radius
        # user_states maps user_id -> dict with keys:
        #   'state': 'off_route' or 'on_route'
        #   'route': dict with route info (id, name, geometry)
        #   'pings': list of (lat, lon, timestamp)
        #   'start_time': timestamp when boarded
        self.user_states = {}
        # lock for thread safety
        self.lock = threading.Lock()

    def _overpass_query(self, lat, lon):
        """
        Query Overpass for any public-transport "route" relations within self.radius meters
        Returns list of relations with geometry and tags.
        """
        # Overpass QL: find relations with route=* around point
        q = f"""
        [out:json];
        (
          relation["type"="route"](around:{self.radius},{lat},{lon});
        );
        out geom tags;
        """
        r = requests.post(OVERPASS_URL, data={"data": q})
        r.raise_for_status()
        data = r.json()
        routes = []
        for rel in data.get("elements", []):
            geom = rel.get("members", [])
            # extract all ways (LineStrings)
            lines = []
            for m in geom:
                if m["type"] == "way" and "geometry" in m:
                    coords = [(pt["lon"], pt["lat"]) for pt in m["geometry"]]
                    lines.append(LineString(coords))
            if not lines:
                continue
            # merge into single multilinestring or polygon if closed
            merged = unary_union(lines)
            # tags
            name = rel["tags"].get("name", rel["tags"].get("ref", "unknown"))
            routes.append({
                "id": rel["id"],
                "name": name,
                "geometry": merged
            })
        return routes

    def _compute_route_area(self, geometry):
        """
        Given a LineString or MultiLineString, buffer slightly and compute area.
        Returns area in square meters.
        """
        # buffer by small amount to produce polygon; buffer distance tuned for area calc
        poly: Polygon = geometry.buffer(1.0)  # 1m buffer
        return poly.area

    def process_ping(self, user_id: str, lat: float, lon: float, timestamp: float):
        """
        Ingest a single GPS ping for user_id at (lat, lon) at UNIX timestamp.
        Returns a Journey dict if the user just completed a journey, otherwise None.
        """
        pt = Point(lon, lat)
        with self.lock:
            state = self.user_states.get(user_id, {"state": "off_route"})
            # if currently off-route, see if we detect boarding
            if state["state"] == "off_route":
                routes = self._overpass_query(lat, lon)
                if not routes:
                    return None
                # choose the route whose geometry is closest
                best = min(routes, key=lambda r: r["geometry"].distance(pt))
                # initialize route tracking
                state = {
                    "state": "on_route",
                    "route": best,
                    "pings": [(lat, lon, timestamp)],
                    "start_time": timestamp,
                }
                # compute and store total route area
                state["route"]["area_sqm"] = self._compute_route_area(best["geometry"])
                self.user_states[user_id] = state
                return None

            # if currently on-route
            else:
                geom = state["route"]["geometry"]
                dist = geom.distance(pt)
                # still on route if within radius (plus small tolerance)
                if dist <= self.radius + 0.5:
                    state["pings"].append((lat, lon, timestamp))
                    return None
                else:
                    # user has left the route → finalize journey
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
                    # reset user state
                    self.user_states[user_id] = {"state": "off_route"}
                    return journey

def gpsinput(user, lat, lon):
    jt = JourneyTracker(radius=10)
    ts = time.time()
    result = jt.process_ping(user, lat, lon, ts)
    return result


