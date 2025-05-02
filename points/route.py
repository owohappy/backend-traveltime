import requests


api_url = "https://transit.land/api/v2/rest/routes"


def get_possible_routes(latitude, longitude):
    """
    Fetch possible routes based on latitude and longitude.
    """
    params = {
    "lat": latitude,
    "lon": longitude,
    "radius": 10,         # Radius in meters (Transitland supports ~bounding box or lat/lon + radius logic)
    "per_page": 20,         # How many results per page
}
    # Example coordinates for testing
    latitude = 37.7749
    longitude = -122.4194

    params["lat"] = latitude
    params["lon"] = longitude
    # Make the API request
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        data = response.json()
        routes = data.get("routes", [])
        return routes
    else:
        response.raise_for_status()


