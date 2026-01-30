"""
Zoom Recordings Resource

This module provides resource definitions for Zoom recordings.
"""

import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel

from zoom_mcp.auth.zoom_auth import ZoomAuth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class RecordingListParams(BaseModel):
    """Parameters for listing recordings."""
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    page_size: int = 30
    page_number: int = 1


class RecordingResource:
    """Resource for interacting with Zoom recordings."""

    def __init__(self, auth_manager: ZoomAuth):
        """
        Initialize the recording resource.
        
        Args:
            auth_manager: The Zoom authentication manager
        """
        self.auth_manager = auth_manager
        logger.info("RecordingResource initialized with auth manager")
    
    async def list_recordings(self, params: RecordingListParams) -> Dict[str, Any]:
        """
        List recordings from Zoom.
        
        Args:
            params: Parameters for listing recordings
            
        Returns:
            Dict containing the list of recordings
        """
        try:
            # Get the access token
            access_token = await self.auth_manager.get_access_token()
            
            # Construct the API URL
            account_id = self.auth_manager.account_id
            if not account_id:
                raise ValueError("Account ID is required but not provided in auth manager")
                
            api_url = f"https://api.zoom.us/v2/accounts/{account_id}/recordings"
            
            # Add query parameters
            query_params = {}
            if params.from_date:
                query_params["from"] = params.from_date
            if params.to_date:
                query_params["to"] = params.to_date
            query_params["page_size"] = params.page_size
            query_params["page_number"] = params.page_number
            
            # Make the API request
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Use httpx for async HTTP requests
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, headers=headers, params=query_params)
                
                if response.status_code != 200:
                    error_message = f"Failed to list recordings: {response.status_code} - {response.text}"
                    logger.error(error_message)
                    raise Exception(error_message)
                
                return response.json()
        
        except Exception as e:
            logger.error(f"Error listing recordings: {str(e)}")
            raise
    
    async def get_recording(self, recording_id: str) -> Dict[str, Any]:
        """
        Get a specific recording from Zoom.
        
        Args:
            recording_id: The ID of the recording to retrieve
            
        Returns:
            Dict containing the recording details
        """
        try:
            # Get the access token
            access_token = await self.auth_manager.get_access_token()
            
            # Construct the API URL
            account_id = self.auth_manager.account_id
            if not account_id:
                raise ValueError("Account ID is required but not provided in auth manager")
                
            api_url = f"https://api.zoom.us/v2/accounts/{account_id}/recordings/{recording_id}"
            
            # Make the API request
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Use httpx for async HTTP requests
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, headers=headers)
                
                if response.status_code != 200:
                    error_message = f"Failed to get recording: {response.status_code} - {response.text}"
                    logger.error(error_message)
                    raise Exception(error_message)
                
                return response.json()
        
        except Exception as e:
            logger.error(f"Error getting recording: {str(e)}")
            raise 