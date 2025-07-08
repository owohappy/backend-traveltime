#!/usr/bin/env python3
"""
Account Management API Test Suite
Tests the enhanced account management endpoints including profile management,
picture uploads, achievements, and preferences.
"""

import requests
import json
import io
import sys
from PIL import Image
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MTE3Njg0MzdhIiwiZXhwIjoxNzUyMDkxODc3fQ.aawVq31NXZ1ucHjxTiSHCamM8zPXpgIFiH2gYhT1sL4"  # Valid test token
TEST_USER_ID = "511768437"  # Valid test user ID

def make_request(method, endpoint, data=None, files=None, params=None):
    """Make HTTP request with authentication"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, files=files)
        elif method == "PUT":
            if files:
                response = requests.put(url, headers=headers, files=files, data=data)
            else:
                response = requests.put(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

def create_test_image():
    """Create a test image for profile picture upload"""
    img = Image.new('RGB', (200, 200), color='#FF6B6B')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

def test_user_points():
    """Test the user points endpoint"""
    print("=== Testing User Points ===")
    
    response = make_request("GET", f"/user/{TEST_USER_ID}/points")
    
    if response and response.status_code == 200:
        data = response.json()
        print(f"✓ User points retrieved successfully")
        print(f"  User ID: {data['user_id']}")
        print(f"  Points: {data['points']}")
        return True
    else:
        print(f"✗ Failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"  Error: {response.text}")
        return False

def test_user_profile():
    """Test the user profile endpoints"""
    print("\n=== Testing User Profile ===")
    
    # Test get profile
    response = make_request("GET", f"/user/{TEST_USER_ID}/profile")
    
    if response and response.status_code == 200:
        data = response.json()
        print(f"✓ User profile retrieved successfully")
        
        if 'data' in data:
            profile = data['data']
            print(f"  Username: {profile['personal_info']['username']}")
            print(f"  Email: {profile['personal_info']['email']}")
            print(f"  Total Points: {profile['points_and_level']['total_points']}")
            print(f"  Level: {profile['points_and_level']['level']}")
            print(f"  Achievements: {len(profile['achievements'])}")
        
        # Test update profile
        update_data = {
            "username": "TestUser_Updated",
            "bio": "Updated bio for testing",
            "privacy_settings": json.dumps({
                "profile_public": True,
                "achievements_public": False
            })
        }
        
        response = make_request("PUT", f"/user/{TEST_USER_ID}/profile", data=update_data)
        
        if response and response.status_code == 200:
            data = response.json()
            print(f"✓ Profile updated successfully")
            print(f"  Updated fields: {data['updated_fields']}")
        else:
            print(f"✗ Profile update failed: {response.status_code if response else 'No response'}")
        
        return True
    else:
        print(f"✗ Failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"  Error: {response.text}")
        return False

def test_profile_picture():
    """Test profile picture upload and retrieval"""
    print("\n=== Testing Profile Picture ===")
    
    # Create test image
    test_image = create_test_image()
    
    # Test upload
    files = {'file': ('test_profile.jpg', test_image, 'image/jpeg')}
    response = make_request("POST", f"/user/{TEST_USER_ID}/picture", files=files)
    
    if response and response.status_code == 200:
        data = response.json()
        print(f"✓ Profile picture uploaded successfully")
        print(f"  Filename: {data['filename']}")
        print(f"  URL: {data['url']}")
        
        # Test retrieve picture
        response = make_request("GET", f"/user/{TEST_USER_ID}/picture")
        
        if response and response.status_code == 200:
            print(f"✓ Profile picture retrieved successfully")
            print(f"  Content type: {response.headers.get('content-type')}")
            print(f"  Size: {len(response.content)} bytes")
        else:
            print(f"✗ Picture retrieval failed: {response.status_code if response else 'No response'}")
        
        return True
    else:
        print(f"✗ Upload failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"  Error: {response.text}")
        return False

def test_user_achievements():
    """Test user achievements endpoint"""
    print("\n=== Testing User Achievements ===")
    
    response = make_request("GET", f"/user/{TEST_USER_ID}/achievements")
    
    if response and response.status_code == 200:
        data = response.json()
        print(f"✓ User achievements retrieved successfully")
        
        if 'data' in data:
            achievements = data['data']
            print(f"  Total achievements: {len(achievements)}")
            
            for achievement in achievements:
                print(f"    {achievement['icon']} {achievement['name']}: {achievement['description']}")
        
        return True
    else:
        print(f"✗ Failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"  Error: {response.text}")
        return False

def test_user_preferences():
    """Test user preferences endpoints"""
    print("\n=== Testing User Preferences ===")
    
    # Test get preferences
    response = make_request("GET", f"/user/{TEST_USER_ID}/preferences")
    
    if response and response.status_code == 200:
        data = response.json()
        print(f"✓ User preferences retrieved successfully")
        
        if 'data' in data:
            preferences = data['data']
            print(f"  Notifications: {preferences.get('notifications', {})}")
            print(f"  Privacy: {preferences.get('privacy', {})}")
            print(f"  App Settings: {preferences.get('app_settings', {})}")
        
        # Test update preferences
        update_preferences = {
            "notifications": {
                "email_notifications": False,
                "push_notifications": True,
                "weekly_summary": True
            },
            "app_settings": {
                "dark_mode": True,
                "language": "de"
            }
        }
        
        response = make_request("PUT", f"/user/{TEST_USER_ID}/preferences", data=update_preferences)
        
        if response and response.status_code == 200:
            data = response.json()
            print(f"✓ Preferences updated successfully")
            print(f"  Updated preferences: {data['updated_preferences']}")
        else:
            print(f"✗ Preferences update failed: {response.status_code if response else 'No response'}")
        
        return True
    else:
        print(f"✗ Failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"  Error: {response.text}")
        return False

def test_legacy_endpoints():
    """Test legacy endpoints for backward compatibility"""
    print("\n=== Testing Legacy Endpoints ===")
    
    # Test legacy getData endpoint
    response = make_request("GET", f"/user/{TEST_USER_ID}/getData")
    
    if response and response.status_code == 200:
        print(f"✓ Legacy getData endpoint works")
    else:
        print(f"✗ Legacy getData failed: {response.status_code if response else 'No response'}")
    
    # Test legacy getDataHours endpoint
    response = make_request("GET", f"/user/{TEST_USER_ID}/getDataHours")
    
    if response and response.status_code == 200:
        print(f"✓ Legacy getDataHours endpoint works")
        return True
    else:
        print(f"✗ Legacy getDataHours failed: {response.status_code if response else 'No response'}")
        return False

def test_authorization():
    """Test authorization and security"""
    print("\n=== Testing Authorization ===")
    
    # Test without token
    url = f"{BASE_URL}/user/{TEST_USER_ID}/profile"
    response = requests.get(url)
    
    if response.status_code == 401 or response.status_code == 403:
        print("✓ Authorization required (as expected)")
    else:
        print(f"✗ Authorization test failed: {response.status_code}")
    
    # Test accessing another user's profile (should fail)
    other_user_id = "99999"
    response = make_request("GET", f"/user/{other_user_id}/profile")
    
    if response and response.status_code == 403:
        print("✓ Cross-user access denied (as expected)")
        return True
    else:
        print(f"✗ Cross-user access test failed: {response.status_code if response else 'No response'}")
        return False

def main():
    """Run all account management tests"""
    print("Starting Account Management API Test Suite")
    print("=" * 50)
    
    # Test results
    results = []
    
    # Run tests
    results.append(test_user_points())
    results.append(test_user_profile())
    results.append(test_profile_picture())
    results.append(test_user_achievements())
    results.append(test_user_preferences())
    results.append(test_legacy_endpoints())
    results.append(test_authorization())
    
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
