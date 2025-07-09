#!/usr/bin/env python3
"""
Test script for manual ride logging API endpoints.
Tests the new /rides/manual endpoints for creating, reading, updating, and deleting manual rides.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "password123"

def print_test_result(test_name, success, details=""):
    """Print formatted test results."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")
    print()

def test_manual_ride_api():
    """Test all manual ride API endpoints."""
    print("=== Manual Ride API Testing ===")
    print(f"Testing against: {BASE_URL}")
    print()
    
    # Step 1: Login to get auth token
    print("1. Authenticating user...")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        if response.status_code == 200:
            auth_data = response.json()
            auth_token = auth_data.get("access_token")
            user_id = auth_data.get("userID")
            
            if auth_token and user_id:
                print_test_result("User authentication", True, f"User ID: {user_id}")
                headers = {"Authorization": f"Bearer {auth_token}"}
            else:
                print_test_result("User authentication", False, "Missing token or user ID")
                return
        else:
            print_test_result("User authentication", False, f"HTTP {response.status_code}: {response.text}")
            return
    except Exception as e:
        print_test_result("User authentication", False, f"Connection error: {str(e)}")
        return
    
    # Step 2: Test manual ride creation
    print("2. Testing manual ride creation...")
    manual_ride_data = {
        "transport_type": "bus",
        "start_location": "Central Station",
        "end_location": "Shopping Mall",
        "duration_minutes": 25,
        "distance_km": 12.5,
        "date": "2025-01-01",
        "time": "14:30",
        "notes": "Test ride entry",
        "manual_entry": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/rides/manual", json=manual_ride_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                ride_id = result.get("ride_id")
                xp_awarded = result.get("xp_awarded", 0)
                print_test_result("Manual ride creation", True, f"Ride ID: {ride_id}, XP: {xp_awarded}")
            else:
                print_test_result("Manual ride creation", False, result.get("error", "Unknown error"))
                return
        else:
            print_test_result("Manual ride creation", False, f"HTTP {response.status_code}: {response.text}")
            return
    except Exception as e:
        print_test_result("Manual ride creation", False, f"Request error: {str(e)}")
        return
    
    # Step 3: Test retrieving manual rides
    print("3. Testing manual ride retrieval...")
    try:
        response = requests.get(f"{BASE_URL}/rides/manual/{user_id}?limit=5", headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                rides = result.get("data", {}).get("rides", [])
                total_count = result.get("data", {}).get("total_count", 0)
                print_test_result("Manual ride retrieval", True, f"Retrieved {total_count} rides")
                
                # Find our test ride
                test_ride = None
                for ride in rides:
                    if ride.get("id") == ride_id:
                        test_ride = ride
                        break
                
                if test_ride:
                    print(f"   Found test ride: {test_ride['transport_type']} from {test_ride['start_location']} to {test_ride['end_location']}")
                else:
                    print_test_result("Find test ride", False, "Created ride not found in list")
            else:
                print_test_result("Manual ride retrieval", False, result.get("error", "Unknown error"))
        else:
            print_test_result("Manual ride retrieval", False, f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print_test_result("Manual ride retrieval", False, f"Request error: {str(e)}")
    
    # Step 4: Test updating manual ride
    print("4. Testing manual ride update...")
    updated_ride_data = {
        "transport_type": "train",
        "start_location": "Central Station",
        "end_location": "Shopping Mall",
        "duration_minutes": 20,
        "distance_km": 12.5,
        "date": "2025-01-01",
        "time": "14:30",
        "notes": "Updated to train service",
        "manual_entry": True
    }
    
    try:
        response = requests.put(f"{BASE_URL}/rides/manual/{ride_id}", json=updated_ride_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print_test_result("Manual ride update", True, result.get("message", "Updated successfully"))
            else:
                print_test_result("Manual ride update", False, result.get("error", "Unknown error"))
        else:
            print_test_result("Manual ride update", False, f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print_test_result("Manual ride update", False, f"Request error: {str(e)}")
    
    # Step 5: Verify the update
    print("5. Verifying ride update...")
    try:
        response = requests.get(f"{BASE_URL}/rides/manual/{user_id}?limit=5", headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                rides = result.get("data", {}).get("rides", [])
                
                # Find our updated ride
                updated_ride = None
                for ride in rides:
                    if ride.get("id") == ride_id:
                        updated_ride = ride
                        break
                
                if updated_ride and updated_ride.get("transport_type") == "train":
                    print_test_result("Verify ride update", True, f"Transport type changed to: {updated_ride['transport_type']}")
                else:
                    print_test_result("Verify ride update", False, "Update not reflected in data")
            else:
                print_test_result("Verify ride update", False, result.get("error", "Unknown error"))
        else:
            print_test_result("Verify ride update", False, f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print_test_result("Verify ride update", False, f"Request error: {str(e)}")
    
    # Step 6: Test ride deletion
    print("6. Testing manual ride deletion...")
    try:
        response = requests.delete(f"{BASE_URL}/rides/manual/{ride_id}", headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print_test_result("Manual ride deletion", True, result.get("message", "Deleted successfully"))
            else:
                print_test_result("Manual ride deletion", False, result.get("error", "Unknown error"))
        else:
            print_test_result("Manual ride deletion", False, f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print_test_result("Manual ride deletion", False, f"Request error: {str(e)}")
    
    # Step 7: Verify deletion
    print("7. Verifying ride deletion...")
    try:
        response = requests.get(f"{BASE_URL}/rides/manual/{user_id}?limit=5", headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                rides = result.get("data", {}).get("rides", [])
                
                # Check that our ride is gone
                deleted_ride = None
                for ride in rides:
                    if ride.get("id") == ride_id:
                        deleted_ride = ride
                        break
                
                if not deleted_ride:
                    print_test_result("Verify ride deletion", True, "Ride successfully removed from database")
                else:
                    print_test_result("Verify ride deletion", False, "Ride still exists after deletion")
            else:
                print_test_result("Verify ride deletion", False, result.get("error", "Unknown error"))
        else:
            print_test_result("Verify ride deletion", False, f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print_test_result("Verify ride deletion", False, f"Request error: {str(e)}")
    
    # Step 8: Test error cases
    print("8. Testing error handling...")
    
    # Test unauthorized access
    try:
        response = requests.post(f"{BASE_URL}/rides/manual", json=manual_ride_data)
        if response.status_code == 200:
            result = response.json()
            if not result.get("success") and "Unauthorized" in result.get("error", ""):
                print_test_result("Unauthorized access handling", True, "Correctly rejected unauthorized request")
            else:
                print_test_result("Unauthorized access handling", False, "Should have rejected unauthorized request")
        else:
            print_test_result("Unauthorized access handling", True, f"HTTP {response.status_code} (expected failure)")
    except Exception as e:
        print_test_result("Unauthorized access handling", False, f"Request error: {str(e)}")
    
    # Test invalid ride ID
    try:
        response = requests.get(f"{BASE_URL}/rides/manual/99999999", headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get("error") and "Access denied" in result.get("error"):
                print_test_result("Invalid user ID handling", True, "Correctly rejected access to other user's data")
            else:
                print_test_result("Invalid user ID handling", False, "Should have rejected access to other user's data")
        else:
            print_test_result("Invalid user ID handling", True, f"HTTP {response.status_code} (expected failure)")
    except Exception as e:
        print_test_result("Invalid user ID handling", False, f"Request error: {str(e)}")
    
    print("=== Manual Ride API Testing Complete ===")

if __name__ == "__main__":
    test_manual_ride_api()
