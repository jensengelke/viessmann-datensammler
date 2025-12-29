# OAuth2 Client with PKCE

A Python OAuth2 client implementation using the Authorization Code flow with PKCE (Proof Key for Code Exchange).

## Features

- ✅ OAuth2 Authorization Code flow with PKCE
- ✅ Automatic PKCE challenge generation (SHA256)
- ✅ Local callback server on `http://localhost:4200`
- ✅ Automatic browser opening for authorization
- ✅ Token exchange and refresh
- ✅ Token persistence (save/load)
- ✅ CSRF protection with state parameter
- ✅ User-friendly HTML callback pages

## Requirements

Install the required Python packages:

```bash
pip install requests
```

The script uses only standard library modules plus `requests`.

## Configuration

Create a `.config.json` file in the same directory as the script with your OAuth2 configuration:

```json
{
  "authorization_endpoint": "https://oauth.example.com/authorize",
  "token_endpoint": "https://oauth.example.com/token",
  "client_id": "your_client_id_here",
  "client_secret": "your_client_secret_here_if_required",
  "redirect_uri": "http://localhost:4200",
  "scope": "read write"
}
```

**For Viessmann Climate Solutions API:**

```json
{
  "authorization_endpoint": "https://iam.viessmann-climatesolutions.com/idp/v3/authorize",
  "token_endpoint": "https://iam.viessmann-climatesolutions.com/idp/v3/token",
  "client_id": "your_client_id_here",
  "redirect_uri": "http://localhost:4200",
  "refresh_token_scope": "IoT User offline_access",
  "installation_id": "your_installation_id_here",
  "gateway_id": "your_gateway_id_here",
  "device_id": "your_device_id_here"
}
```

### Required Fields

- `authorization_endpoint`: The OAuth2 authorization URL
- `token_endpoint`: The OAuth2 token endpoint URL
- `client_id`: Your OAuth2 client ID
- `redirect_uri`: Must be `http://localhost:4200` (or configure the port as needed)
- `scope` or `refresh_token_scope`: Space-separated list of OAuth2 scopes

### Required Fields for Viessmann API (collect-data.py)

- `installation_id`: Your Viessmann installation ID
- `gateway_id`: Your Viessmann gateway ID
- `device_id`: Your Viessmann device ID

### Optional Fields

- `client_secret`: Client secret (only if required by your OAuth2 server)

## Usage

### First Time Authentication

Run the script:

```bash
python oauth2_client.py
```

The script will:

1. Load configuration from `.config.json`
2. Generate PKCE challenge and verifier
3. Create an authorization URL
4. Open your default browser to the authorization page
5. Start a local web server on `http://localhost:4200`
6. Wait for the OAuth2 callback
7. Exchange the authorization code for access and refresh tokens
8. Save tokens to `tokens.json`

### Using Existing Tokens

If `tokens.json` exists, the script will:

1. Load the existing tokens
2. Ask if you want to refresh the access token
3. If yes, use the refresh token to get a new access token

### Token Refresh

To refresh an expired access token:

```bash
python oauth2_client.py
```

Select "yes" when prompted to refresh the token.

## Programmatic Usage

You can also use the `OAuth2Client` class in your own code:

```python
from oauth2_client import OAuth2Client

# Initialize client
client = OAuth2Client('.config.json')

# Try to load existing tokens
if not client.load_tokens():
    # No existing tokens, perform authorization flow
    auth_url = client.generate_authorization_url()
    print(f"Please visit: {auth_url}")
    
    # Start callback server and get code
    from oauth2_client import start_callback_server
    code, state = start_callback_server(port=4200)
    
    if code:
        # Exchange code for tokens
        client.exchange_code_for_tokens(code)
        client.save_tokens()

# Use the access token
print(f"Access Token: {client.access_token}")

# Make authenticated API requests
import requests
headers = {
    'Authorization': f'{client.token_type} {client.access_token}'
}
response = requests.get('https://api.example.com/data', headers=headers)
```

## Files

- `oauth2_client.py`: Main OAuth2 client implementation
- `.config.json`: OAuth2 configuration (create this file)
- `.config.json.example`: Example configuration template
- `tokens.json`: Stored access and refresh tokens (auto-generated)

## Security Notes

1. **Keep `.config.json` and `tokens.json` secure** - Add them to `.gitignore`
2. **PKCE** provides additional security by preventing authorization code interception
3. **State parameter** protects against CSRF attacks
4. **Tokens are stored locally** - Ensure proper file permissions

## Troubleshooting

### Port Already in Use

If port 4200 is already in use, you can modify the port in your `.config.json`:

```json
{
  "redirect_uri": "http://localhost:8080"
}
```

Make sure to register this new redirect URI with your OAuth2 provider.

### Browser Doesn't Open

If the browser doesn't open automatically, copy the authorization URL from the console and paste it into your browser manually.

### Token Refresh Fails

If token refresh fails, the script will automatically start a new authorization flow.

## How PKCE Works

1. **Code Verifier**: A cryptographically random string (43-128 characters)
2. **Code Challenge**: SHA256 hash of the code verifier, base64url encoded
3. **Authorization Request**: Includes the code challenge
4. **Token Request**: Includes the original code verifier
5. **Server Verification**: Server hashes the verifier and compares with the challenge

This prevents authorization code interception attacks, even without a client secret.

## License

This is a utility script for OAuth2 authentication. Use it as needed for your projects.
