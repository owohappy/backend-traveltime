#!/usr/bin/env python3
"""
Quick test for cross-user access
"""

import requests

BASE_URL = "http://localhost:8001"
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4NjE1MzE5MjFhIiwiZXhwIjoxNzUyMDg3MTkxfQ.1H-BeneZTpy080le8cq2LC7JpSGRwBoyMJFcz1R9JMk"

def test_cross_user_access():
    """Test accessing another user's profile (should fail)"""
    other_user_id = "99999"
    url = f"{BASE_URL}/user/{other_user_id}/profile"
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 403:
            print("✓ Cross-user access correctly denied")
            return True
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return False

if __name__ == "__main__":
    test_cross_user_access()
