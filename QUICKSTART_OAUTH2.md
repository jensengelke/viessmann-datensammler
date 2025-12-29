# Quick Start Guide - OAuth2 Client

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure OAuth2 Settings

Edit your `.config.json` file with your OAuth2 provider's details:

```json
{
  "authorization_endpoint": "https://your-oauth-server.com/oauth/authorize",
  "token_endpoint": "https://your-oauth-server.com/oauth/token",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret_if_needed",
  "redirect_uri": "http://localhost:4200",
  "scope": "your required scopes"
}
```

**Note:** The `.config.json` file is already in your `.gitignore` to keep credentials secure.

## Step 3: Run the OAuth2 Client

```bash
python oauth2_client.py
```

This will:
1. Open your browser for authorization
2. Start a local server on port 4200
3. Receive the authorization code
4. Exchange it for access and refresh tokens
5. Save tokens to `tokens.json`

## Step 4: Use the Access Token

The tokens are saved in `tokens.json`. You can use them in your application:

```python
from oauth2_client import OAuth2Client

client = OAuth2Client('.config.json')
client.load_tokens()

# Use the access token in your API requests
print(f"Access Token: {client.access_token}")
```

Or use the example script:

```bash
python example_api_request.py
```

## Files Created

- **`oauth2_client.py`** - Main OAuth2 client with PKCE implementation
- **`example_api_request.py`** - Example showing how to make authenticated API calls
- **`.config.json.example`** - Template for your configuration
- **`README_OAUTH2.md`** - Detailed documentation
- **`requirements.txt`** - Python dependencies

## Important Notes

1. **Security**: Both `.config.json` and `tokens.json` contain sensitive data and should be in `.gitignore`
2. **Redirect URI**: Make sure `http://localhost:4200` is registered with your OAuth2 provider
3. **Port Conflicts**: If port 4200 is in use, change it in `.config.json` and re-register with your OAuth provider
4. **Token Refresh**: The client automatically handles token refresh when needed

## Troubleshooting

**Browser doesn't open?**
- Copy the URL from the console and paste it manually in your browser

**Port already in use?**
- Change the port in `.config.json` redirect_uri
- Update the redirect URI with your OAuth provider

**Token expired?**
- Run `python oauth2_client.py` and choose to refresh the token
- Or delete `tokens.json` and re-authenticate

## Next Steps

After authentication, you can use the access token to make API requests to your REST API. See `example_api_request.py` for a complete example.
