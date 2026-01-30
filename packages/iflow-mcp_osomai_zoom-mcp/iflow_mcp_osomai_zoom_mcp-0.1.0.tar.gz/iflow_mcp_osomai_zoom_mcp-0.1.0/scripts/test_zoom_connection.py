#!/usr/bin/env python3
"""
Test Zoom API Connection

This script tests the connection to the Zoom API using the ZoomAuth class.
"""

import os
import sys
import json
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.zoom_mcp.auth.zoom_auth import ZoomAuth

def test_oauth_token():
    """Test getting an OAuth token."""
    print("\n===== Testing OAuth Token Generation =====")
    
    try:
        auth = ZoomAuth.from_env()
        token = auth.get_access_token()
        print(f"✅ Successfully generated OAuth token: {token[:10]}...{token[-10:]}")
        return token
    except Exception as e:
        print(f"❌ Failed to generate OAuth token: {str(e)}")
        return None

def test_account_settings(token):
    """Test getting account settings."""
    print("\n===== Testing Account Settings Access =====")
    
    if not token:
        print("❌ Skipping test: No valid token available")
        return False
    
    import httpx
    
    try:
        # Use the correct endpoint for account settings
        response = httpx.get(
            "https://api.zoom.us/v2/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Successfully accessed user information")
            return True
        else:
            print(f"❌ Failed to access user information: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error accessing user information: {str(e)}")
        return False

def test_recordings_access(token):
    """Test access to recordings."""
    print("\n===== Testing Recordings Access =====")
    
    if not token:
        print("❌ Skipping test: No valid token available")
        return False
    
    import httpx
    from datetime import datetime, timedelta
    
    # Get user information first to get user ID
    try:
        user_response = httpx.get(
            "https://api.zoom.us/v2/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if user_response.status_code != 200:
            print(f"❌ Failed to get user information: {user_response.text}")
            return False
            
        user_data = user_response.json()
        user_id = user_data.get("id")
        
        if not user_id:
            print("❌ Failed to get user ID from user information")
            return False
            
        print(f"Found user ID: {user_id}")
        
        # Get recordings from the last 30 days
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        response = httpx.get(
            f"https://api.zoom.us/v2/users/{user_id}/recordings",
            params={
                "from": start_date,
                "to": end_date,
                "page_size": 5  # Limit to 5 recordings
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            recordings_count = len(data.get("meetings", []))
            print(f"✅ Successfully accessed recordings. Found {recordings_count} recordings.")
            return True
        else:
            print(f"❌ Failed to access recordings: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error accessing recordings: {str(e)}")
        return False

def main():
    """Run the tests."""
    print(f"Running Zoom API connection tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test OAuth token generation
    token = test_oauth_token()
    
    # Test account settings access
    test_account_settings(token)
    
    # Test recordings access
    test_recordings_access(token)
    
    print("\n===== Test Summary =====")
    print(f"Tests completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()