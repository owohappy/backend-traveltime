#!/usr/bin/env python3
"""
API Verification Script
Quick test to verify all major API endpoints are working
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_public_endpoints():
    """Test public endpoints"""
    print("🔍 Testing Public Endpoints:")
    
    # Health check
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("  ✅ Health check: OK")
    else:
        print(f"  ❌ Health check failed: {response.status_code}")
    
    # API docs
    response = requests.get(f"{BASE_URL}/docs")
    if response.status_code == 200:
        print("  ✅ API documentation: Available")
    else:
        print(f"  ❌ API docs failed: {response.status_code}")

def test_authentication():
    """Test authentication endpoints"""
    print("\n🔐 Testing Authentication:")
    
    # Registration
    user_data = {
        "email": "apitest@example.com",
        "password": "password123",
        "name": "API Test User",
        "username": "apitest",
        "phonenumber": "1234567890",
        "address": "123 API St"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=user_data)
    if response.status_code == 201:
        data = response.json()
        token = data["access_token"]
        user_id = str(data["userID"])
        print(f"  ✅ Registration successful: User ID {user_id}")
        return token, user_id
    else:
        print(f"  ❌ Registration failed: {response.status_code}")
        print(f"      Error: {response.text}")
        return None, None

def test_user_endpoints(token, user_id):
    """Test user management endpoints"""
    if not token or not user_id:
        print("\n❌ Cannot test user endpoints - no valid token")
        return
    
    print(f"\n👤 Testing User Endpoints (User ID: {user_id}):")
    headers = {"Authorization": f"Bearer {token}"}
    
    # User points
    response = requests.get(f"{BASE_URL}/user/{user_id}/points", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ User points: {data['points']} points")
    else:
        print(f"  ❌ User points failed: {response.status_code}")
    
    # User profile
    response = requests.get(f"{BASE_URL}/user/{user_id}/profile", headers=headers)
    if response.status_code == 200:
        data = response.json()
        email = data['data']['personal_info']['email']
        print(f"  ✅ User profile: {email}")
    else:
        print(f"  ❌ User profile failed: {response.status_code}")
    
    # User achievements
    response = requests.get(f"{BASE_URL}/user/{user_id}/achievements", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ User achievements: {len(data['data'])} achievements")
    else:
        print(f"  ❌ User achievements failed: {response.status_code}")
    
    # User preferences
    response = requests.get(f"{BASE_URL}/user/{user_id}/preferences", headers=headers)
    if response.status_code == 200:
        print("  ✅ User preferences: Retrieved successfully")
    else:
        print(f"  ❌ User preferences failed: {response.status_code}")

def test_authorization():
    """Test authorization controls"""
    print("\n🛡️ Testing Authorization:")
    
    # Test without token
    response = requests.get(f"{BASE_URL}/user/12345/profile")
    if response.status_code in [401, 403]:
        print("  ✅ Authorization required (as expected)")
    else:
        print(f"  ❌ Authorization bypass: {response.status_code}")

def main():
    """Run comprehensive API verification"""
    print("🚀 TravelTime API Verification Script")
    print("=" * 50)
    
    # Test sequence
    test_public_endpoints()
    token, user_id = test_authentication()
    test_user_endpoints(token, user_id)
    test_authorization()
    
    print("\n" + "=" * 50)
    print("✅ API Verification Complete!")
    print("\n📋 Current Working Test Credentials:")
    print(f"   Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MTE3Njg0MzdhIiwiZXhwIjoxNzUyMDkxODc3fQ.aawVq31NXZ1ucHjxTiSHCamM8zPXpgIFiH2gYhT1sL4")
    print(f"   User ID: 511768437")
    print(f"   Email: test2@example.com")
    print("\n🔗 Access API Documentation: http://localhost:8001/docs")

if __name__ == "__main__":
    main()
