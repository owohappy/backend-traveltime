#!/usr/bin/env python3
"""
Route Performance Test Script

This script tests the performance improvements of the new route management system
with lazy loading and spatial indexing.
"""

import time
import random
import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TOKEN = "your_test_token_here"  # Replace with valid JWT

# Test coordinates around Berlin
TEST_COORDINATES = [
    (52.5200, 13.4050),  # Alexanderplatz
    (52.5170, 13.3888),  # Brandenburg Gate
    (52.5074, 13.4256),  # Potsdamer Platz
    (52.5109, 13.4413),  # Checkpoint Charlie
    (52.5244, 13.4105),  # Museum Island
    (52.4963, 13.4266),  # Tempelhof
    (52.4675, 13.4021),  # Schöneberg
    (52.5560, 13.3500),  # Wedding
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

def test_route_cache_status():
    """Test the route cache status endpoint"""
    print("=== Testing Route Cache Status ===")
    
    response = make_request("GET", "/admin/routes/status")
    
    if response and response.status_code == 200:
        data = response.json()
        cache_info = data['data']['cache_status']
        route_info = data['data']['route_manager']
        
        print("✓ Cache status retrieved successfully")
        print(f"  Cache file size: {cache_info['file_size_mb']} MB")
        print(f"  Routes loaded: {route_info['routes_loaded']}")
        print(f"  Total routes: {route_info['total_routes']}")
        print(f"  Spatial index cells: {route_info['spatial_index_cells']}")
        print(f"  Estimated memory usage: {route_info['memory_usage_estimated_mb']} MB")
        
        return True
    else:
        print(f"✗ Failed: {response.status_code if response else 'No response'}")
        return False

def test_nearby_routes_performance():
    """Test the performance of nearby route lookups"""
    print("\n=== Testing Nearby Routes Performance ===")
    
    total_time = 0
    successful_requests = 0
    
    for i, (lat, lon) in enumerate(TEST_COORDINATES):
        print(f"Testing coordinate {i+1}/{len(TEST_COORDINATES)}: ({lat}, {lon})")
        
        start_time = time.time()
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "radius": 1000
        }
        
        response = make_request("GET", "/gps/routes/nearby", params=params)
        
        end_time = time.time()
        request_time = end_time - start_time
        total_time += request_time
        
        if response and response.status_code == 200:
            data = response.json()
            route_count = data['data']['route_analysis']['nearby_routes_count']
            on_route = data['data']['route_analysis']['on_transport_route']
            
            print(f"  ✓ {request_time:.3f}s - Found {route_count} routes, On route: {on_route}")
            successful_requests += 1
        else:
            print(f"  ✗ {request_time:.3f}s - Failed: {response.status_code if response else 'No response'}")
    
    if successful_requests > 0:
        avg_time = total_time / successful_requests
        print(f"\nPerformance Summary:")
        print(f"  Average request time: {avg_time:.3f}s")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Successful requests: {successful_requests}/{len(TEST_COORDINATES)}")
        
        if avg_time < 0.5:
            print("  🚀 Excellent performance!")
        elif avg_time < 1.0:
            print("  ✅ Good performance")
        else:
            print("  ⚠️  Performance could be improved")
    
    return successful_requests > 0

def test_gps_tracking_performance():
    """Test GPS tracking endpoint performance"""
    print("\n=== Testing GPS Tracking Performance ===")
    
    # Simulate multiple GPS pings
    user_id = "1"
    total_time = 0
    successful_requests = 0
    
    for i in range(10):  # 10 GPS pings
        lat, lon = random.choice(TEST_COORDINATES)
        
        # Add some random variation to simulate movement
        lat += random.uniform(-0.001, 0.001)
        lon += random.uniform(-0.001, 0.001)
        
        location_data = {
            "user_id": user_id,
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "accuracy": random.uniform(3.0, 15.0),
            "speed": random.uniform(0.0, 15.0)
        }
        
        start_time = time.time()
        response = make_request("POST", f"/gps/track/{user_id}", data=location_data)
        end_time = time.time()
        
        request_time = end_time - start_time
        total_time += request_time
        
        if response and response.status_code == 200:
            data = response.json()
            session_type = data['data']['session_info']['type']
            on_transport = data['data']['travel_status'] == 'on_transport'
            
            print(f"  Ping {i+1:2d}: {request_time:.3f}s - {session_type}, Transport: {on_transport}")
            successful_requests += 1
        else:
            print(f"  Ping {i+1:2d}: {request_time:.3f}s - Failed")
        
        time.sleep(0.1)  # Small delay between pings
    
    if successful_requests > 0:
        avg_time = total_time / successful_requests
        print(f"\nGPS Tracking Performance:")
        print(f"  Average tracking time: {avg_time:.3f}s")
        print(f"  Successful pings: {successful_requests}/10")
    
    return successful_requests > 0

def test_cache_refresh():
    """Test the cache refresh functionality"""
    print("\n=== Testing Cache Refresh ===")
    
    print("Triggering cache refresh...")
    start_time = time.time()
    
    response = make_request("POST", "/admin/routes/refresh")
    
    end_time = time.time()
    refresh_time = end_time - start_time
    
    if response and response.status_code == 200:
        data = response.json()
        server_refresh_time = data['data']['refresh_duration_seconds']
        route_count = data['data']['total_routes_loaded']
        
        print(f"✓ Cache refresh completed in {refresh_time:.1f}s")
        print(f"  Server reported: {server_refresh_time:.1f}s")
        print(f"  Routes loaded: {route_count}")
        print(f"  Spatial index rebuilt: {data['data']['spatial_index_rebuilt']}")
        
        return True
    else:
        print(f"✗ Cache refresh failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"  Error: {response.text}")
        return False

def main():
    """Run all performance tests"""
    print("Route Performance Test Suite")
    print("=" * 50)
    
    if TEST_TOKEN == "your_test_token_here":
        print("⚠️  Warning: Please update TEST_TOKEN with a valid JWT token")
        print()
    
    # Run all tests
    tests = [
        ("Route Cache Status", test_route_cache_status),
        ("Nearby Routes Performance", test_nearby_routes_performance),
        ("GPS Tracking Performance", test_gps_tracking_performance),
        ("Cache Refresh", test_cache_refresh),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*20} Test Summary {'='*20}")
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Route system is performing well.")
    elif passed >= total * 0.7:
        print("⚠️  Most tests passed, but some issues detected.")
    else:
        print("❌ Multiple test failures detected. Check system configuration.")

if __name__ == "__main__":
    main()
