#!/usr/bin/env python3
"""
Example: Using OAuth2 Client to Make Authenticated API Requests

This script demonstrates how to use the OAuth2Client to authenticate
and make API requests with the obtained access token.
"""

import requests
from oauth2_client import OAuth2Client, start_callback_server
import webbrowser
from urllib.parse import urlparse


def get_authenticated_client():
    """
    Get an authenticated OAuth2 client with a valid access token.
    
    Returns:
        OAuth2Client instance with valid access token
    """
    # Initialize client
    client = OAuth2Client('.config.json')
    
    # Try to load existing tokens
    if client.load_tokens():
        print("✓ Loaded existing tokens")
        
        # Optionally try to refresh if token might be expired
        # You could add logic here to check expiration time
        try:
            print("Attempting to refresh access token...")
            client.refresh_access_token()
            print("✓ Token refreshed successfully")
            client.save_tokens()
        except Exception as e:
            print(f"Note: Could not refresh token: {e}")
            print("Using existing token (may need re-authentication if expired)")
    else:
        print("No existing tokens found. Starting authentication flow...")
        
        # Generate authorization URL
        auth_url = client.generate_authorization_url()
        print(f"\nAuthorization URL: {auth_url}\n")
        
        # Open browser
        webbrowser.open(auth_url)
        
        # Start callback server
        port = int(urlparse(client.config['redirect_uri']).port or 4200)
        code, state = start_callback_server(port=port)
        
        if not code:
            raise Exception("Failed to receive authorization code")
        
        if state != client.state:
            raise Exception("State parameter mismatch - possible CSRF attack!")
        
        # Exchange code for tokens
        print("\nExchanging code for tokens...")
        client.exchange_code_for_tokens(code)
        print("✓ Tokens obtained successfully")
        
        # Save tokens for future use
        client.save_tokens()
    
    return client


def make_api_request(client, url, method='GET', **kwargs):
    """
    Make an authenticated API request.
    
    Args:
        client: OAuth2Client instance with valid access token
        url: API endpoint URL
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        **kwargs: Additional arguments to pass to requests
        
    Returns:
        Response object
    """
    # Add authorization header
    headers = kwargs.get('headers', {})
    headers['Authorization'] = f'{client.token_type} {client.access_token}'
    kwargs['headers'] = headers
    
    # Make request
    response = requests.request(method, url, **kwargs)
    
    # Handle token expiration (401 Unauthorized)
    if response.status_code == 401:
        print("Access token expired. Attempting to refresh...")
        try:
            client.refresh_access_token()
            client.save_tokens()
            
            # Retry request with new token
            headers['Authorization'] = f'{client.token_type} {client.access_token}'
            response = requests.request(method, url, **kwargs)
        except Exception as e:
            print(f"Failed to refresh token: {e}")
            raise
    
    return response


def main():
    """Example usage of the OAuth2 client."""
    print("=" * 60)
    print("OAuth2 API Request Example")
    print("=" * 60)
    print()
    
    try:
        # Get authenticated client
        client = get_authenticated_client()
        
        print()
        print("=" * 60)
        print("Ready to make API requests!")
        print("=" * 60)
        print()
        
        api_url = "https://api.viessmann-climatesolutions.com/iot/v2/features/installations/2211174/gateways/7736172039937224/devices/0/features"
        
        print(f"Making GET request to: {api_url}")
        response = make_api_request(client, api_url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            print("Response Body:")
            print(response.text)
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
