#!/usr/bin/env python3
"""
Check Environment Variables

This script checks and prints the environment variables used for Zoom API authentication.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main function."""
    print("🔍 Checking Environment Variables...\n")
    
    # Get environment variables
    api_key = os.getenv("ZOOM_API_KEY")
    api_secret = os.getenv("ZOOM_API_SECRET")
    account_id = os.getenv("ZOOM_ACCOUNT_ID")
    
    # Print environment variables
    print(f"ZOOM_API_KEY: {api_key}")
    print(f"ZOOM_API_SECRET: {'*' * len(api_secret) if api_secret else 'Not set'}")
    print(f"ZOOM_ACCOUNT_ID: {account_id}")
    
    # Check if all required variables are set
    if api_key and api_secret and account_id:
        print("\n✅ All required environment variables are set.")
    else:
        print("\n❌ Some required environment variables are missing:")
        if not api_key:
            print("- ZOOM_API_KEY is not set")
        if not api_secret:
            print("- ZOOM_API_SECRET is not set")
        if not account_id:
            print("- ZOOM_ACCOUNT_ID is not set")
    
    print("\nRecommendations:")
    print("1. Verify that these values match the ones in your Zoom Marketplace app.")
    print("2. Make sure your Zoom app is activated in the Zoom Marketplace.")
    print("3. Check that your Zoom app has the necessary scopes enabled.")
    print("4. Ensure your Zoom account has the required permissions (Pro, Business, or Enterprise).")


if __name__ == "__main__":
    main() 