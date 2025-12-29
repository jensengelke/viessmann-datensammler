#!/usr/bin/env python3
"""
Token Refresh Test Script

This script demonstrates how to refresh an access token using an existing refresh token.
It's useful for testing the token refresh flow without going through the full authorization.
"""

from oauth2_client import OAuth2Client
import json


def main():
    """Test token refresh functionality."""
    print("=" * 60)
    print("OAuth2 Token Refresh Test")
    print("=" * 60)
    print()
    
    try:
        # Initialize OAuth2 client
        client = OAuth2Client('.config.json')
        print("✓ Configuration loaded")
        print()
        
        # Load existing tokens
        if not client.load_tokens('tokens.json'):
            print("✗ No tokens.json file found!")
            print("Please run oauth2_client.py first to obtain initial tokens.")
            return
        
        print("Current token information:")
        print(f"  Access Token: {client.access_token[:30] if client.access_token else 'None'}...")
        print(f"  Refresh Token: {client.refresh_token[:30] if client.refresh_token else 'None'}...")
        print(f"  Token Type: {client.token_type}")
        print(f"  Expires In: {client.expires_in} seconds")
        print()
        
        if not client.refresh_token:
            print("✗ No refresh token available!")
            print("Please run oauth2_client.py first to obtain a refresh token.")
            return
        
        # Refresh the access token
        print("Refreshing access token...")
        print(f"Token endpoint: {client.config['token_endpoint']}")
        print(f"Client ID: {client.config['client_id']}")
        print()
        
        token_response = client.refresh_access_token()
        
        print("✓ Token refreshed successfully!")
        print()
        print("New token information:")
        print(f"  Access Token: {client.access_token[:30]}...")
        print(f"  Refresh Token: {client.refresh_token[:30] if client.refresh_token else 'Not updated'}...")
        print(f"  Token Type: {client.token_type}")
        print(f"  Expires In: {client.expires_in} seconds")
        print()
        
        # Save the new tokens
        client.save_tokens('tokens.json')
        
        print("=" * 60)
        print("Token refresh complete!")
        print("=" * 60)
        
        # Show full response for debugging
        print()
        print("Full token response:")
        print(json.dumps(token_response, indent=2))
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
