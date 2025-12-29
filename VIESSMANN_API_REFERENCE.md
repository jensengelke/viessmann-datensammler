# Viessmann Climate Solutions API - Quick Reference

## OAuth2 Configuration

Your `.config.json` should look like this:

```json
{
  "authorization_endpoint": "https://iam.viessmann-climatesolutions.com/idp/v3/authorize",
  "token_endpoint": "https://iam.viessmann-climatesolutions.com/idp/v3/token",
  "client_id": "YOUR_CLIENT_ID_HERE",
  "redirect_uri": "http://localhost:4200",
  "refresh_token_scope": "IoT User offline_access"
}
```

### Important Notes:

- **No client_secret needed** - Viessmann uses PKCE for public clients
- **Scopes**: `IoT User offline_access` (space-separated)
  - `IoT` - Access to IoT devices
  - `User` - User information
  - `offline_access` - Enables refresh token

## Token Refresh

The OAuth2 client automatically handles token refresh. The refresh request looks like:

```bash
curl -X POST "https://iam.viessmann-climatesolutions.com/idp/v3/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token&client_id=YOUR_CLIENT_ID&refresh_token=YOUR_REFRESH_TOKEN"
```

This is already implemented in the `refresh_access_token()` method.

## Usage Workflows

### 1. First Time Authentication

```bash
# Make sure your .config.json is configured
python oauth2_client.py
```

This will:
1. Open browser for authorization
2. Get authorization code
3. Exchange for access + refresh tokens
4. Save to `tokens.json`

### 2. Refresh Existing Token

```bash
# Test token refresh
python test_token_refresh.py
```

Or programmatically:

```python
from oauth2_client import OAuth2Client

client = OAuth2Client('.config.json')
client.load_tokens()
client.refresh_access_token()
client.save_tokens()
```

### 3. Make API Requests

```python
from oauth2_client import OAuth2Client
import requests

# Load client with tokens
client = OAuth2Client('.config.json')
client.load_tokens()

# Make authenticated request
headers = {
    'Authorization': f'{client.token_type} {client.access_token}'
}

response = requests.get(
    'https://api.viessmann.com/iot/v1/equipment/installations',
    headers=headers
)

print(response.json())
```

## Token Lifecycle

1. **Initial Authorization** → Access Token (expires in ~1 hour) + Refresh Token (long-lived)
2. **Access Token Expires** → Use Refresh Token to get new Access Token
3. **Refresh Token** → May or may not be rotated (depends on Viessmann's implementation)

## Files

- `.config.json` - OAuth2 configuration (gitignored)
- `tokens.json` - Stored tokens (gitignored)
- `oauth2_client.py` - Main OAuth2 client
- `test_token_refresh.py` - Test token refresh
- `example_api_request.py` - Example API usage

## Troubleshooting

### "Invalid refresh token"
- Your refresh token may have expired
- Run `python oauth2_client.py` to re-authenticate

### "Invalid client"
- Check your `client_id` in `.config.json`
- Ensure redirect_uri matches what's registered

### "Invalid scope"
- Ensure scopes are: `IoT User offline_access`
- Check for typos in `refresh_token_scope`

## API Endpoints (Viessmann)

Once authenticated, you can access:

- **Installations**: `GET https://api.viessmann.com/iot/v1/equipment/installations`
- **Gateways**: `GET https://api.viessmann.com/iot/v1/equipment/gateways`
- **Devices**: `GET https://api.viessmann.com/iot/v1/equipment/installations/{installationId}/gateways/{gatewaySerial}/devices`
- **Features**: `GET https://api.viessmann.com/iot/v1/equipment/installations/{installationId}/gateways/{gatewaySerial}/devices/{deviceId}/features`

All requests require the `Authorization: Bearer {access_token}` header.
