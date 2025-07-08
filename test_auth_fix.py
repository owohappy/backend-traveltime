#!/usr/bin/env python3
"""
Quick test script to verify the authentication fix
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"

def test_authentication():
    """Test authentication and profile access"""
    print("Testing authentication and profile access...")
    
    # Test login first
    login_data = {
        "username": "test@example.com",  # Replace with a valid test user
        "password": "testpassword"        # Replace with valid password
    }
    
    try:
        # Attempt login
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            
            if token:
                print("✓ Login successful, got token")
                
                # Test profile access
                headers = {"Authorization": f"Bearer {token}"}
                profile_response = requests.get(f"{BASE_URL}/user/123/profile", headers=headers)
                
                print(f"Profile response status: {profile_response.status_code}")
                if profile_response.status_code == 200:
                    print("✓ Profile access successful - authentication fix worked!")
                    return True
                else:
                    print(f"✗ Profile access failed: {profile_response.text}")
                    return False
            else:
                print("✗ No token received from login")
                return False
        else:
            print(f"✗ Login failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False

def test_ping():
    """Test simple ping endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/ping")
        if response.status_code == 200:
            print("✓ Ping test successful")
            return True
        else:
            print(f"✗ Ping test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Ping test failed: {e}")
        return False

if __name__ == "__main__":
    print("Quick Authentication Test")
    print("=" * 30)
    
    # Test basic connectivity
    if test_ping():
        # Test authentication
        test_authentication()
    else:
        print("API is not responding")
