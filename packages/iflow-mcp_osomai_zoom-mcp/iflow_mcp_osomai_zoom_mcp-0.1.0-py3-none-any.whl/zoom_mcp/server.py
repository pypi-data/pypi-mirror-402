"""
Zoom MCP Server

This module provides the main implementation of the Zoom MCP server.
"""

import os
import json
import logging

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from zoom_mcp.auth.zoom_auth import ZoomAuth
from zoom_mcp.resources.recordings import RecordingListParams, RecordingResource
from zoom_mcp.tools.recordings import (
    GetRecordingTranscriptParams,
    get_recording_transcript as get_recording_transcript_tool,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class ZoomMCP:
    """
    Zoom MCP Server implementation.

    This class provides a Model Context Protocol (MCP) server for Zoom,
    allowing LLMs to interact with Zoom data and functionality.
    """

    def __init__(self):
        """Initialize the Zoom MCP server."""
        try:
            # Initialize auth manager from environment variables
            self.auth_manager = ZoomAuth.from_env()
            
            self.mcp_server = FastMCP("Zoom")
            # Add name attribute for MCP CLI
            self.name = "Zoom"

            # Register resources and tools
            self._register_resources()
            self._register_tools()
        except Exception as e:
            logger.error(f"Error initializing Zoom MCP server: {str(e)}")
            raise

    def _register_resources(self):
        """Register all Zoom resources with the MCP server."""
        # Register recording resources
        recording_resource = RecordingResource(self.auth_manager)

        @self.mcp_server.resource("recordings://list")
        async def list_recordings() -> str:
            """List recordings from Zoom"""
            # Since there's no URI parameter, we pass an empty params object
            recordings = await recording_resource.list_recordings(RecordingListParams())
            return json.dumps(recordings)

        @self.mcp_server.resource("recording://{recording_id}")
        async def get_recording(recording_id: str) -> str:
            """Get a specific recording from Zoom"""
            recording = await recording_resource.get_recording(recording_id)
            return json.dumps(recording)

    def _register_tools(self):
        """Register all Zoom tools with the MCP server."""
        @self.mcp_server.tool()
        async def get_recording_transcript(params: GetRecordingTranscriptParams) -> str:
            """
            Get the transcript for a Zoom recording.
            
            Args:
                params: Parameters for retrieving the recording transcript
                
            Returns:
                JSON string containing the transcript data
            """
            try:
                transcript_data = await get_recording_transcript_tool(params)
                return json.dumps(transcript_data.dict())
            except Exception as e:
                logger.error(f"Error in get_recording_transcript tool: {str(e)}")
                raise

    def start(self):
        """Start the MCP server."""
        self.mcp_server.run()

    def stop(self):
        """Stop the MCP server."""
        # Cleanup resources if needed
        pass


def create_zoom_mcp() -> ZoomMCP:
    """
    Create and configure a Zoom MCP server instance.
    
    Returns:
        Configured ZoomMCP instance
    """
    return ZoomMCP()


# Create a standard variable that MCP CLI can recognize
# This will be used when running `mcp install src/zoom_mcp/server.py`
# The actual configuration will be loaded from environment variables

# Load environment variables from .env file
load_dotenv()

# Create the server instance with a standard variable name
# This is the variable that MCP CLI will look for
try:
    server = create_zoom_mcp()
except Exception as e:
    logger.error(f"Error creating Zoom MCP server: {str(e)}")
    # Create a placeholder server for MCP CLI discovery
    # The actual server will be created when run with proper environment variables
    server = None


if __name__ == "__main__":
    try:
        # Create and start the MCP server
        mcp_server = create_zoom_mcp()
        
        # Run the server
        mcp_server.start()
    except Exception as e:
        logger.error(f"Error starting Zoom MCP server: {str(e)}")
        import sys
        sys.exit(1) 