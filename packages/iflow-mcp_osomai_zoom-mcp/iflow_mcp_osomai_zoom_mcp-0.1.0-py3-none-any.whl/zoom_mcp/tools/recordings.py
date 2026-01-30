"""
Zoom Recordings Tool

This module provides tools for working with Zoom recordings, including
retrieving and processing recording transcripts.
"""

import logging
import re
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from zoom_mcp.auth.zoom_auth import ZoomAuth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class GetRecordingTranscriptParams(BaseModel):
    """Parameters for retrieving a recording transcript."""
    recording_url: str = Field(..., description="URL of the Zoom recording")
    include_speaker_labels: bool = Field(True, description="Include speaker labels in the transcript")


class RecordingTranscriptResponse(BaseModel):
    """Response model for recording transcript."""
    transcript: List[Dict[str, Any]] = Field(..., description="List of transcript segments")
    recording_id: str = Field(..., description="ID of the recording")
    duration: int = Field(..., description="Duration of the recording in seconds")


def extract_recording_id(recording_url: str) -> str:
    """
    Extract the recording ID from a Zoom recording URL.
    
    Args:
        recording_url: The URL of the Zoom recording
        
    Returns:
        The recording ID
        
    Raises:
        ValueError: If the recording ID cannot be extracted from the URL
    """
    # Example URL: https://zoom.us/rec/share/abcdef123456
    pattern = r"zoom\.us/rec/(?:share|play)/([a-zA-Z0-9_-]+)"
    match = re.search(pattern, recording_url)
    
    if not match:
        raise ValueError(f"Could not extract recording ID from URL: {recording_url}")
    
    return match.group(1)


async def get_recording_transcript(params: GetRecordingTranscriptParams) -> RecordingTranscriptResponse:
    """
    Retrieve the transcript for a Zoom recording.
    
    Args:
        params: Parameters for retrieving the recording transcript
        
    Returns:
        The recording transcript response
        
    Raises:
        Exception: If the transcript cannot be retrieved
    """
    try:
        recording_id = extract_recording_id(params.recording_url)
        logger.info(f"Retrieving transcript for recording ID: {recording_id}")
        
        # Initialize Zoom auth from environment variables
        zoom_auth = ZoomAuth.from_env()
        
        # Get the access token
        access_token = await zoom_auth.get_access_token()
        
        # Construct the API URL for retrieving the recording transcript
        account_id = zoom_auth.account_id
        api_url = f"https://api.zoom.us/v2/accounts/{account_id}/recordings/{recording_id}/transcript"
        
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
                error_message = f"Failed to retrieve transcript: {response.status_code} - {response.text}"
                logger.error(error_message)
                raise Exception(error_message)
            
            data = response.json()
            
            # Process the transcript data
            transcript_segments = []
            for segment in data.get("recording_transcripts", []):
                transcript_segment = {
                    "start_time": segment.get("start_time"),
                    "end_time": segment.get("end_time"),
                    "text": segment.get("text"),
                }
                
                if params.include_speaker_labels and "speaker" in segment:
                    transcript_segment["speaker"] = segment.get("speaker")
                
                transcript_segments.append(transcript_segment)
            
            # Create the response
            return RecordingTranscriptResponse(
                transcript=transcript_segments,
                recording_id=recording_id,
                duration=data.get("duration", 0)
            )
    
    except Exception as e:
        logger.error(f"Error retrieving recording transcript: {str(e)}")
        raise 