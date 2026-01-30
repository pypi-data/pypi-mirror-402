# Zoom MCP Server

A Model Context Protocol (MCP) server implementation for Zoom, providing AI models with access to Zoom's API capabilities.

## Overview

This project implements an MCP server that enables Claude to connect to Zoom, retrieve data, and perform actions through the Zoom API. It serves as a bridge between Claude and Zoom, allowing for seamless integration and access to Zoom meetings, users, and recordings.

## Features

- Connect to Zoom using Server-to-Server OAuth 2.0 authentication
- Retrieve user information and profiles
- Access meeting details and recordings
- Query Zoom account settings and configurations
- Manage Zoom resources through a standardized API
- Debug mode for troubleshooting API connections

## Installation

### Prerequisites

- Python 3.11 or higher
- A Zoom account with admin privileges
- A Zoom Server-to-Server OAuth app with appropriate scopes
- [uv](https://github.com/astral-sh/uv) for Python package management

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/zoom-mcp.git
   cd zoom-mcp
   ```

2. Create a virtual environment and activate it using uv:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies using uv:
   ```bash
   uv pip install -e .
   ```

4. Set up Zoom API credentials:
   ```bash
   python scripts/setup_zoom_auth.py
   ```
   This script will guide you through setting up your Zoom API credentials in a `.env` file:
   ```
   ZOOM_API_KEY=your-client-id
   ZOOM_API_SECRET=your-client-secret
   ZOOM_ACCOUNT_ID=your-account-id
   ```

## Usage

### Testing the Connection

After setting up your credentials, you can test the connection to the Zoom API:

```bash
python scripts/test_zoom_connection.py
```

This script will verify:
- Your environment variables are set correctly
- OAuth token generation works
- Basic API access is successful

### API Endpoints

The MCP server provides access to various Zoom API endpoints:

- `/users/me` - Get information about the authenticated user
- Additional endpoints will be implemented as needed

## Authentication

This project uses Zoom's Server-to-Server OAuth 2.0 authentication. The authentication module handles:
- OAuth 2.0 token generation
- Token caching and renewal
- Environment variable configuration

The authentication flow:
1. Base64 encode the API Key and Secret for Basic authentication
2. Request an access token from Zoom's OAuth endpoint
3. Use the token for subsequent API requests
4. Automatically refresh the token when it expires

## Development

### Creating a Zoom App

1. Go to the [Zoom App Marketplace](https://marketplace.zoom.us/) and sign in
2. Click "Develop" in the top-right corner and select "Build App"
3. Choose "Server-to-Server OAuth" app type
4. Fill in the required information for your app
5. In the "Scopes" section, add the following scopes:
   - `user:read:admin` (required for basic user information)
   - Additional scopes as needed for your specific use case

### Running Tests
```bash
python -m pytest
```

### Code Style
This project follows PEP 8 guidelines. You can check your code style using:
```bash
uv pip install flake8
flake8 src tests
```

## Troubleshooting

If you encounter issues with the Zoom API connection:

1. **Authentication Errors**
   - Verify your API Key and Secret are correct
   - Ensure your app has the necessary scopes enabled
   - Deactivate and reactivate your app in the Zoom Marketplace

2. **Permission Errors**
   - Check that your account has the required permissions
   - Verify that the scopes requested match the endpoints you're trying to access

3. **Account ID Issues**
   - Make sure you're using the correct Account ID from your Zoom account profile
   - The Account ID is required for Server-to-Server OAuth apps

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 