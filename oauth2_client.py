#!/usr/bin/env python3
"""
OAuth2 Client with PKCE Flow

This script implements the OAuth2 authorization code flow with PKCE (Proof Key for Code Exchange).
It reads configuration from .config.json and handles the complete authentication flow.
"""

import json
import hashlib
import base64
import secrets
import webbrowser
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import threading


class OAuth2Client:
    """OAuth2 client with PKCE support."""
    
    def __init__(self, config_file='.config.json'):
        """
        Initialize the OAuth2 client.
        
        Args:
            config_file: Path to the configuration file containing OAuth2 parameters
        """
        self.config = self._load_config(config_file)
        self.code_verifier = None
        self.code_challenge = None
        self.authorization_code = None
        self.access_token = None
        self.refresh_token = None
        self.token_type = None
        self.expires_in = None
        
    def _load_config(self, config_file):
        """Load OAuth2 configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Validate required fields
            required_fields = [
                'authorization_endpoint',
                'token_endpoint',
                'client_id',
                'redirect_uri'
            ]
            
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field in config: {field}")
            
            # Validate that either 'scope' or 'refresh_token_scope' is present
            if 'scope' not in config and 'refresh_token_scope' not in config:
                raise ValueError("Missing required field in config: 'scope' or 'refresh_token_scope'")
            
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def _generate_code_verifier(self):
        """Generate a cryptographically random code verifier for PKCE."""
        # Generate 32 random bytes and base64url encode them
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
        # Remove padding
        return code_verifier.rstrip('=')
    
    def _generate_code_challenge(self, code_verifier):
        """
        Generate code challenge from code verifier using SHA256.
        
        Args:
            code_verifier: The code verifier string
            
        Returns:
            Base64url encoded SHA256 hash of the code verifier
        """
        # Hash the code verifier with SHA256
        digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        # Base64url encode and remove padding
        code_challenge = base64.urlsafe_b64encode(digest).decode('utf-8')
        return code_challenge.rstrip('=')
    
    def generate_authorization_url(self):
        """
        Generate the OAuth2 authorization URL with PKCE parameters.
        
        Returns:
            The complete authorization URL for the user to visit
        """
        # Generate PKCE parameters
        self.code_verifier = self._generate_code_verifier()
        self.code_challenge = self._generate_code_challenge(self.code_verifier)
        
        # Build authorization URL parameters
        params = {
            'response_type': 'code',
            'client_id': self.config['client_id'],
            'redirect_uri': self.config['redirect_uri'],
            'scope': self.config.get('refresh_token_scope') or self.config.get('scope'),
            'code_challenge': self.code_challenge,
            'code_challenge_method': 'S256'
        }
        
        # Add optional state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        params['state'] = state
        self.state = state
        
        # Construct the full URL
        auth_url = f"{self.config['authorization_endpoint']}?{urlencode(params)}"
        return auth_url
    
    def exchange_code_for_tokens(self, authorization_code):
        """
        Exchange the authorization code for access and refresh tokens.
        
        Args:
            authorization_code: The authorization code received from the callback
            
        Returns:
            Dictionary containing token information
        """
        token_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.config['redirect_uri'],
            'client_id': self.config['client_id'],
            'code_verifier': self.code_verifier
        }
        
        # Add client_secret if provided in config (some OAuth2 servers require it)
        if 'client_secret' in self.config:
            token_data['client_secret'] = self.config['client_secret']
        
        try:
            response = requests.post(
                self.config['token_endpoint'],
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()
            
            token_response = response.json()
            
            # Store tokens
            self.access_token = token_response.get('access_token')
            self.refresh_token = token_response.get('refresh_token')
            self.token_type = token_response.get('token_type', 'Bearer')
            self.expires_in = token_response.get('expires_in')
            
            return token_response
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to exchange code for tokens: {e}")
    
    def refresh_access_token(self):
        """
        Refresh the access token using the refresh token.
        
        Returns:
            Dictionary containing new token information
        """
        if not self.refresh_token:
            raise ValueError("No refresh token available")
        
        token_data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.config['client_id']
        }
        
        # Add client_secret if provided in config
        if 'client_secret' in self.config:
            token_data['client_secret'] = self.config['client_secret']
        
        try:
            response = requests.post(
                self.config['token_endpoint'],
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()
            
            token_response = response.json()
            
            # Update tokens
            self.access_token = token_response.get('access_token')
            if 'refresh_token' in token_response:
                self.refresh_token = token_response['refresh_token']
            self.token_type = token_response.get('token_type', 'Bearer')
            self.expires_in = token_response.get('expires_in')
            
            return token_response
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to refresh access token: {e}")
    
    def save_tokens(self, filename='tokens.json'):
        """
        Save tokens to a file for later use.
        
        Args:
            filename: Path to save the tokens
        """
        tokens = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_type': self.token_type,
            'expires_in': self.expires_in
        }
        
        with open(filename, 'w') as f:
            json.dump(tokens, f, indent=2)
        
        print(f"Tokens saved to {filename}")
    
    def load_tokens(self, filename='tokens.json'):
        """
        Load tokens from a file.
        
        Args:
            filename: Path to load the tokens from
        """
        try:
            with open(filename, 'r') as f:
                tokens = json.load(f)
            
            self.access_token = tokens.get('access_token')
            self.refresh_token = tokens.get('refresh_token')
            self.token_type = tokens.get('token_type', 'Bearer')
            self.expires_in = tokens.get('expires_in')
            
            print(f"Tokens loaded from {filename}")
            return True
        except FileNotFoundError:
            print(f"Token file not found: {filename}")
            return False


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth2 callback."""
    
    def do_GET(self):
        """Handle GET request from OAuth2 redirect."""
        # Parse the query parameters
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        # Extract authorization code
        if 'code' in query_params:
            self.server.authorization_code = query_params['code'][0]
            self.server.state = query_params.get('state', [None])[0]
            
            # Send success response to browser
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            success_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authorization Successful</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background-color: #f0f0f0;
                    }
                    .container {
                        background-color: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        text-align: center;
                    }
                    .success {
                        color: #28a745;
                        font-size: 24px;
                        margin-bottom: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success">✓ Authorization Successful!</div>
                    <p>You can close this window and return to the application.</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(success_html.encode())
            
        elif 'error' in query_params:
            error = query_params['error'][0]
            error_description = query_params.get('error_description', ['Unknown error'])[0]
            
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authorization Failed</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background-color: #f0f0f0;
                    }}
                    .container {{
                        background-color: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        text-align: center;
                    }}
                    .error {{
                        color: #dc3545;
                        font-size: 24px;
                        margin-bottom: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error">✗ Authorization Failed</div>
                    <p><strong>Error:</strong> {error}</p>
                    <p>{error_description}</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode())
            self.server.authorization_code = None
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def start_callback_server(port=4200, timeout=300):
    """
    Start a local HTTP server to receive the OAuth2 callback.
    
    Args:
        port: Port number to listen on (default: 4200)
        timeout: Maximum time to wait for callback in seconds (default: 300)
        
    Returns:
        Tuple of (authorization_code, state) or (None, None) if timeout
    """
    server = HTTPServer(('localhost', port), CallbackHandler)
    server.authorization_code = None
    server.state = None
    server.timeout = 1  # Check every second
    
    print(f"Starting callback server on http://localhost:{port}")
    print(f"Waiting for authorization callback (timeout: {timeout}s)...")
    
    # Run server in a loop with timeout
    start_time = 0
    while server.authorization_code is None and start_time < timeout:
        server.handle_request()
        start_time += 1
    
    if server.authorization_code:
        print("Authorization code received!")
        return server.authorization_code, server.state
    else:
        print("Timeout waiting for authorization callback")
        return None, None


def main():
    """Main function to run the OAuth2 flow."""
    print("=" * 60)
    print("OAuth2 Client with PKCE Flow")
    print("=" * 60)
    print()
    
    try:
        # Initialize OAuth2 client
        client = OAuth2Client('.config.json')
        print("✓ Configuration loaded successfully")
        print()
        
        # Try to load existing tokens
        if client.load_tokens():
            print("✓ Existing tokens loaded")
            print()
            choice = input("Do you want to refresh the access token? (y/n): ").strip().lower()
            if choice == 'y':
                try:
                    tokens = client.refresh_access_token()
                    print("✓ Access token refreshed successfully")
                    print()
                    print("New Token Information:")
                    print(f"  Access Token: {client.access_token[:20]}...")
                    print(f"  Token Type: {client.token_type}")
                    print(f"  Expires In: {client.expires_in} seconds")
                    client.save_tokens()
                    return
                except Exception as e:
                    print(f"✗ Failed to refresh token: {e}")
                    print("Proceeding with new authorization flow...")
                    print()
            else:
                print()
                print("Current Token Information:")
                print(f"  Access Token: {client.access_token[:20]}...")
                print(f"  Token Type: {client.token_type}")
                return
        
        # Generate authorization URL
        auth_url = client.generate_authorization_url()
        print("Authorization URL generated:")
        print(auth_url)
        print()
        
        # Open browser automatically
        print("Opening browser for authorization...")
        webbrowser.open(auth_url)
        print()
        
        # Start callback server
        port = int(urlparse(client.config['redirect_uri']).port or 4200)
        authorization_code, state = start_callback_server(port=port)
        
        if not authorization_code:
            print("✗ Failed to receive authorization code")
            return
        
        # Verify state parameter (CSRF protection)
        if state != client.state:
            print("✗ State parameter mismatch - possible CSRF attack!")
            return
        
        print()
        print("Exchanging authorization code for tokens...")
        
        # Exchange code for tokens
        tokens = client.exchange_code_for_tokens(authorization_code)
        
        print("✓ Tokens obtained successfully!")
        print()
        print("Token Information:")
        print(f"  Access Token: {client.access_token[:20]}...")
        print(f"  Refresh Token: {client.refresh_token[:20] if client.refresh_token else 'N/A'}...")
        print(f"  Token Type: {client.token_type}")
        print(f"  Expires In: {client.expires_in} seconds")
        print()
        
        # Save tokens
        client.save_tokens()
        
        print()
        print("=" * 60)
        print("Authentication complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
