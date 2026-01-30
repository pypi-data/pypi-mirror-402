"""
Zoom MCP CLI

This module provides a command-line interface for the Zoom MCP server.
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

from zoom_mcp.server import create_zoom_mcp

# Load environment variables from .env file
# Try to load from current directory and parent directories
env_path = Path.cwd() / '.env'
if not env_path.exists():
    # Try to load from the script's directory
    env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try to load from any parent directory
    load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Zoom MCP Server")
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> None:
    """
    Main entry point for the Zoom MCP CLI.
    
    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
    """
    parsed_args = parse_args(args)
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, parsed_args.log_level))
    
    try:
        # Create the MCP server
        mcp_server = create_zoom_mcp()
        
        # Start the server
        logger.info("Starting Zoom MCP server")
        mcp_server.start()
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()