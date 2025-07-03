#!/usr/bin/env python3
"""
GPS Tracking API Test Script

This script tests the enhanced GPS location tracking endpoints to ensure they work correctly.
It simulates a user journey on public transportation.
"""

import requests
import json
import time
from datetime import datetime, timedelta
import random

# Test configuration
BASE_URL = "http://localhost:8000"  # Adjust if your server runs on different port
TEST_USER_ID = "1"  # Adjust to a valid user ID in your system
TEST_TOKEN = "your_test_token_here"  # Replace with a valid JWT token

# Sample GPS coordinates (Berlin public transport route)
ROUTE_COORDINATES = [
    (52.5200, 13.4050),  # Alexanderplatz
    (52.5208, 13.4094),  # Moving along route
    (52.5219, 13.4124),  # Continuing 
    (52.5235, 13.4155),  # S-Bahn route
    (52.5251, 13.4186),  # Approaching station
    (52.5270, 13.4220),  # Friedrichstraße
]

OFF_ROUTE_COORDINATES = [
    (52.5100, 13.3900),  # Off the transport route
    (52.5050, 13.3850),  # Walking/not on transport
]

def make_request(method, endpoint, data=None, params=None):
    """Make HTTP request with authentication"""
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}",
        "Content-Type": "application/json"
    }
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def test_gps_tracking():
    """Test the main GPS tracking endpoint"""
    print("=== Testing GPS Tracking Endpoint ===")
    
    for i, (lat, lon) in enumerate(ROUTE_COORDINATES):
        print(f"\nStep {i+1}: Sending GPS coordinates ({lat}, {lon})")
        
        location_data = {
            "user_id": TEST_USER_ID,
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "accuracy": random.uniform(3.0, 15.0),  # Simulated GPS accuracy
            "speed": random.uniform(5.0, 20.0),     # Simulated speed in m/s
            "bearing": random.uniform(0, 360)       # Simulated direction
        }
        
        response = make_request("POST", f"/gps/track/{TEST_USER_ID}", data=location_data)
        
        if response and response.status_code == 200:
            data = response.json()
            print(f"✓ Success: {data['data']['session_info']['type']} session")
            print(f"  Transport: {data['data']['session_info']['transport_type']}")
            print(f"  Duration: {data['data']['session_info']['duration_seconds']:.1f}s")
            print(f"  Distance: {data['data']['session_info']['distance_km']:.3f}km")
        else:
            print(f"✗ Failed: {response.status_code if response else 'No response'}")
            if response:
                print(f"  Error: {response.text}")
        
        time.sleep(2)  # Simulate time between GPS pings

def test_tracking_status():
    """Test the tracking status endpoint"""
    print("\n=== Testing Tracking Status Endpoint ===")
    
    response = make_request("GET", f"/gps/status/{TEST_USER_ID}")
    
    if response and response.status_code == 200:
        data = response.json()
        print("✓ Status retrieved successfully")
        print(f"  Active session: {data['data']['tracking_status']['is_active_session']}")
        print(f"  Daily trips: {data['data']['travel_statistics']['daily']['trip_count']}")
        print(f"  User XP: {data['data']['user_profile']['total_xp']}")
    else:
        print(f"✗ Failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"  Error: {response.text}")

def test_nearby_routes():
    """Test the nearby routes endpoint"""
    print("\n=== Testing Nearby Routes Endpoint ===")
    
    lat, lon = ROUTE_COORDINATES[0]  # Use first coordinate
    params = {
        "latitude": lat,
        "longitude": lon,
        "radius": 500
    }
    
    response = make_request("GET", "/gps/routes/nearby", params=params)
    
    if response and response.status_code == 200:
        data = response.json()
        print("✓ Nearby routes retrieved successfully")
        print(f"  Routes found: {data['data']['route_analysis']['nearby_routes_count']}")
        print(f"  On transport route: {data['data']['route_analysis']['on_transport_route']}")
        print(f"  Transport type: {data['data']['route_analysis']['detected_transport_type']}")
    else:
        print(f"✗ Failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"  Error: {response.text}")

def test_session_end():
    """Test ending a session by going off-route"""
    print("\n=== Testing Session End (Off-Route) ===")
    
    for i, (lat, lon) in enumerate(OFF_ROUTE_COORDINATES):
        print(f"\nOff-route step {i+1}: GPS coordinates ({lat}, {lon})")
        
        location_data = {
            "user_id": TEST_USER_ID,
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        response = make_request("POST", f"/gps/track/{TEST_USER_ID}", data=location_data)
        
        if response and response.status_code == 200:
            data = response.json()
            print(f"✓ Response: {data['data']['session_info']['type']} session")
            
            if data['data']['session_info']['type'] == 'ended':
                print(f"  🎉 Session completed!")
                print(f"  Total duration: {data['data']['session_info']['duration_seconds']:.1f}s")
                print(f"  Total distance: {data['data']['session_info']['distance_km']:.3f}km")
                if 'rewards' in data['data']:
                    print(f"  XP awarded: {data['data']['rewards']['xp_awarded']}")
        else:
            print(f"✗ Failed: {response.status_code if response else 'No response'}")
        
        time.sleep(2)

def main():
    """Run all GPS tracking tests"""
    print("GPS Tracking API Test Suite")
    print("=" * 40)
    
    if TEST_TOKEN == "your_test_token_here":
        print("⚠️  Warning: Please update TEST_TOKEN with a valid JWT token")
        print("⚠️  Warning: Ensure TEST_USER_ID corresponds to a valid user")
        print()
    
    # Test sequence simulating a complete journey
    test_tracking_status()  # Check initial status
    test_nearby_routes()    # Check route availability
    test_gps_tracking()     # Simulate journey on transport
    test_session_end()      # Go off-route to end session
    test_tracking_status()  # Check final status
    
    print("\n=== Test Suite Complete ===")

if __name__ == "__main__":
    main()
