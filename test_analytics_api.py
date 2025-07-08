#!/usr/bin/env python3
"""
Test the analytics API endpoints.
"""

import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
TEST_TOKEN = "test_token_123"  # Update with valid token
TEST_USER_ID = "12345"

def make_request(method, endpoint, data=None, params=None):
    """Make HTTP request with auth header."""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

def test_popular_routes():
    """Test the popular routes analytics endpoint"""
    print("=== Testing Popular Routes Analytics ===")
    
    # Test with default limit
    response = make_request("GET", "/analytics/popular-routes")
    
    if response and response.status_code == 200:
        data = response.json()
        popular_routes = data['data']['popular_routes']
        
        print(f"✓ Popular routes retrieved successfully")
        print(f"  Found {len(popular_routes)} popular routes")
        print(f"  Total routes analyzed: {data['data']['total_routes_analyzed']}")
        
        if popular_routes:
            top_route = popular_routes[0]
            print(f"  Top route: {top_route['route_id']} (usage: {top_route['usage_count']})")
            print(f"  Confidence: {top_route['analytics']['confidence']}")
        
        # Test with custom limit
        response = make_request("GET", "/analytics/popular-routes", params={"limit": 5})
        if response and response.status_code == 200:
            data = response.json()
            print(f"  Custom limit test: {len(data['data']['popular_routes'])} routes (limit: 5)")
        
        return True
    else:
        print(f"✗ Failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"  Error: {response.text}")
        return False

def test_operator_statistics():
    """Test the operator statistics endpoint"""
    print("\n=== Testing Operator Statistics ===")
    
    response = make_request("GET", "/analytics/operator-stats")
    
    if response and response.status_code == 200:
        data = response.json()
        operators = data['data']['operators']
        summary = data['data']['summary']
        
        print(f"✓ Operator statistics retrieved successfully")
        print(f"  Total operators: {summary['total_operators']}")
        print(f"  Total routes: {summary['total_routes']}")
        print(f"  Transport types: {len(summary['transport_type_distribution'])}")
        
        if operators:
            top_operator = operators[0]
            print(f"  Top operator: {top_operator['operator']}")
            print(f"  Market share: {top_operator['market_share']}%")
            print(f"  Routes: {top_operator['total_routes']}")
            print(f"  Transport types: {list(top_operator['transport_types'].keys())}")
        
        # Display transport type distribution
        print("  Transport type distribution:")
        for transport_type, stats in summary['transport_type_distribution'].items():
            print(f"    {transport_type}: {stats['count']} routes ({stats['percentage']}%)")
        
        return True
    else:
        print(f"✗ Failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"  Error: {response.text}")
        return False

def test_transport_patterns():
    """Test the transport patterns analytics endpoint"""
    print("\n=== Testing Transport Patterns Analytics ===")
    
    response = make_request("GET", "/analytics/transport-patterns")
    
    if response and response.status_code == 200:
        data = response.json()
        patterns = data['data']['transport_patterns']
        accuracy = data['data']['detection_accuracy']
        
        print(f"✓ Transport patterns retrieved successfully")
        print(f"  Transport types analyzed: {accuracy['total_transport_types']}")
        print(f"  High confidence patterns: {accuracy['high_confidence_patterns']}")
        print(f"  Total learning samples: {accuracy['total_learning_samples']}")
        print(f"  Overall confidence: {accuracy['overall_confidence']}")
        
        if patterns:
            print("  Pattern details:")
            for transport_type, pattern in patterns.items():
                print(f"    {transport_type}:")
                print(f"      Confidence: {pattern['confidence']}")
                print(f"      Samples: {pattern['sample_count']}")
                print(f"      Stop frequency: {pattern['stop_frequency']}")
                print(f"      Status: {pattern['learning_status']}")
                
                if pattern['speed_statistics']:
                    speed_stats = pattern['speed_statistics']
                    print(f"      Avg speed: {speed_stats['avg_speed']} km/h")
                    print(f"      Speed range: {speed_stats['min_speed']}-{speed_stats['max_speed']} km/h")
        
        return True
    else:
        print(f"✗ Failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"  Error: {response.text}")
        return False

def test_user_travel_insights():
    """Test the user travel insights endpoint"""
    print("\n=== Testing User Travel Insights ===")
    
    response = make_request("GET", f"/analytics/user/{TEST_USER_ID}/travel-insights")
    
    if response and response.status_code == 200:
        data = response.json()
        
        if 'travel_insights' in data['data'] and data['data']['travel_insights']:
            insights = data['data']['travel_insights']
            summary = insights['travel_summary']
            preferences = insights['transport_preferences']
            
            print(f"✓ User travel insights retrieved successfully")
            print(f"  User ID: {data['data']['user_id']}")
            print(f"  Total trips: {summary['total_trips']}")
            print(f"  Total distance: {summary['total_distance_km']} km")
            print(f"  Total duration: {summary['total_duration_hours']} hours")
            print(f"  Avg trip distance: {summary['avg_trip_distance']} km")
            print(f"  Preferred transport: {preferences['preferred_transport']}")
            print(f"  Transport diversity: {preferences['transport_diversity']}")
            
            if 'efficiency_metrics' in insights:
                efficiency = insights['efficiency_metrics']
                print(f"  Average speed: {efficiency['avg_speed_kmh']} km/h")
                print(f"  Consistency score: {efficiency['consistency_score']}")
            
            print(f"  Data reliability: {data['data']['data_quality']['reliability']}")
        else:
            print(f"✓ No travel data found for user {TEST_USER_ID}")
        
        return True
    else:
        print(f"✗ Failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"  Error: {response.text}")
        return False

def test_analytics_dashboard():
    """Test the analytics dashboard endpoint"""
    print("\n=== Testing Analytics Dashboard ===")
    
    response = make_request("GET", "/analytics/dashboard")
    
    if response and response.status_code == 200:
        data = response.json()
        dashboard = data['data']
        
        print(f"✓ Analytics dashboard retrieved successfully")
        print(f"  Refresh interval: {data['refresh_interval']} seconds")
        
        # System overview
        overview = dashboard['system_overview']
        print(f"  System Overview:")
        print(f"    Total routes: {overview['total_routes']}")
        print(f"    Routes cached: {overview['routes_cached']}")
        print(f"    Unique routes used: {overview['unique_routes_used']}")
        print(f"    Total usage events: {overview['total_usage_events']}")
        print(f"    System health: {overview['system_health']}")
        
        # Popular routes
        popular = dashboard['popular_routes']
        print(f"  Popular Routes (Top 5):")
        for i, route in enumerate(popular[:3], 1):
            print(f"    {i}. Route {route['route_id']}: {route['usage_count']} uses ({route['percentage']}%)")
        
        # Transport analytics
        transport = dashboard['transport_analytics']
        print(f"  Transport Analytics:")
        print(f"    Total operators: {transport['total_operators']}")
        print(f"    Transport types detected: {transport['transport_types_detected']}")
        print(f"    High confidence patterns: {transport['high_confidence_patterns']}")
        print(f"    Learning samples: {transport['total_learning_samples']}")
        
        # Performance metrics
        performance = dashboard['performance_metrics']
        print(f"  Performance Metrics:")
        print(f"    Cache efficiency: {performance['cache_efficiency']}%")
        print(f"    Route coverage: {performance['route_coverage']}%")
        print(f"    Pattern learning rate: {performance['pattern_learning_rate']}")
        
        return True
    else:
        print(f"✗ Failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"  Error: {response.text}")
        return False

def test_authentication():
    """Test authentication requirements"""
    print("\n=== Testing Authentication ===")
    
    # Test without token
    url = f"{BASE_URL}/analytics/popular-routes"
    response = requests.get(url)
    
    if response.status_code == 401 or (response.status_code == 200 and "AUTH_INVALID" in response.text):
        print("✓ Authentication required (as expected)")
        return True
    else:
        print(f"✗ Authentication test failed: {response.status_code}")
        return False

def main():
    """Run all analytics tests"""
    print("Starting Analytics API Test Suite")
    print("=" * 50)
    
    # Test results
    results = []
    
    # Run tests
    results.append(test_authentication())
    results.append(test_popular_routes())
    results.append(test_operator_statistics())
    results.append(test_transport_patterns())
    results.append(test_user_travel_insights())
    results.append(test_analytics_dashboard())
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total} tests")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
