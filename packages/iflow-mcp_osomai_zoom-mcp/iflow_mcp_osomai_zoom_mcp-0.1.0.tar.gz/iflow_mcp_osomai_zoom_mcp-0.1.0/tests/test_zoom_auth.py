"""Tests for Zoom authentication module."""

import os
import pytest
from datetime import datetime, timedelta
from zoom_mcp.auth.zoom_auth import ZoomAuth

@pytest.fixture
def zoom_auth():
    """Create a ZoomAuth instance for testing."""
    return ZoomAuth(
        api_key="test_api_key",
        api_secret="test_api_secret",
        account_id="test_account_id"
    )

def test_init(zoom_auth):
    """Test ZoomAuth initialization."""
    assert zoom_auth.api_key == "test_api_key"
    assert zoom_auth.api_secret == "test_api_secret"
    assert zoom_auth.account_id == "test_account_id"
    assert zoom_auth._token is None
    assert zoom_auth._token_expiry is None

def test_get_access_token(zoom_auth):
    """Test access token generation and retrieval."""
    token = zoom_auth.get_access_token()
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0

def test_token_reuse(zoom_auth):
    """Test that the same token is reused if still valid."""
    token1 = zoom_auth.get_access_token()
    token2 = zoom_auth.get_access_token()
    assert token1 == token2

def test_token_expiry(zoom_auth):
    """Test that a new token is generated after expiry."""
    # Get initial token
    token1 = zoom_auth.get_access_token()
    
    # Manually set expiry to past
    zoom_auth._token_expiry = datetime.now() - timedelta(hours=1)
    
    # Get new token
    token2 = zoom_auth.get_access_token()
    assert token1 != token2

def test_from_env():
    """Test creating ZoomAuth instance from environment variables."""
    # Set up test environment variables
    os.environ["ZOOM_API_KEY"] = "env_api_key"
    os.environ["ZOOM_API_SECRET"] = "env_api_secret"
    os.environ["ZOOM_ACCOUNT_ID"] = "env_account_id"
    
    try:
        auth = ZoomAuth.from_env()
        assert auth.api_key == "env_api_key"
        assert auth.api_secret == "env_api_secret"
        assert auth.account_id == "env_account_id"
    finally:
        # Clean up environment variables
        del os.environ["ZOOM_API_KEY"]
        del os.environ["ZOOM_API_SECRET"]
        del os.environ["ZOOM_ACCOUNT_ID"]

def test_from_env_missing_required():
    """Test that missing required environment variables raise ValueError."""
    # Remove required environment variables if they exist
    if "ZOOM_API_KEY" in os.environ:
        del os.environ["ZOOM_API_KEY"]
    if "ZOOM_API_SECRET" in os.environ:
        del os.environ["ZOOM_API_SECRET"]
    
    with pytest.raises(ValueError):
        ZoomAuth.from_env() 