#!/usr/bin/env python3
"""
Example: Using OAuth2 Client to Make Authenticated API Requests

This script collects all features from our heatpump and updates a Google sheet
"""

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
from oauth2_client import OAuth2Client, start_callback_server
import os.path
from urllib.parse import urlparse
import webbrowser
from datetime import datetime
import pytz
import json

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
        
        # Get installation, gateway, and device IDs from config
        installation_id = client.config.get('installation_id')
        gateway_id = client.config.get('gateway_id')
        device_id = client.config.get('device_id')
                
        # Validate that required IDs are present
        if not installation_id or not gateway_id or not device_id:
            raise ValueError(
                "Missing required configuration fields. Please add 'installation_id', "
                "'gateway_id', and 'device_id' to your .config.json file."
            )
        
        print()
        print("=" * 60)
        print("Ready to make API requests!")
        print("=" * 60)
        print()
        
        api_url = f"https://api.viessmann-climatesolutions.com/iot/v2/features/installations/{installation_id}/gateways/{gateway_id}/devices/{device_id}/features"
        
        print(f"Making GET request to: {api_url}")
        response = make_api_request(client, api_url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            # Parse JSON response into dictionary
            data = response.json()
            print(f"Successfully retrieved {len(data)} features")
            print(f"Data type: {type(data)}")
            
            # Save response to local file
            with open('all-features.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("Response saved to all-features.json")
            
            # Extract outside temperature
            outside_temperature = None
            curve_slope = None
            curve_shift = None
            comfort_temperature = None
            normal_temperature = None
            vorlauf_temperature = None
            vorlauf_secondary_temperature = None
            if 'data' in data:
                for feature in data['data']:
                    if feature.get('feature') == 'heating.sensors.temperature.outside':
                        try:
                            outside_temperature = feature['properties']['value']['value']
                            print(f"\nOutside Temperature: {outside_temperature}°C")
                            continue
                        except (KeyError, TypeError) as e:
                            print(f"Error extracting temperature: {e}")
                            continue
                    if feature.get('feature') == 'heating.circuits.0.heating.curve':
                        try:
                            curve_slope = feature['properties']['slope']['value']
                            curve_shift = feature['properties']['shift']['value']
                            print(f"\nCurve Slope: {curve_slope}")
                            print(f"\nCurve Shift: {curve_shift}")
                            continue
                        except (KeyError, TypeError) as e:
                            print(f"Error extracting heating curve: {e}")
                            continue
                    if feature.get('feature') == 'heating.circuits.0.operating.programs.comfortHeating':
                        try:
                            comfort_temperature = feature['properties']['temperature']['value']
                            print(f"\nComfort Temperature: {comfort_temperature}")
                            continue
                        except (KeyError, TypeError) as e:
                            print(f"Error extracting comfort temperature: {e}")
                            continue
                    if feature.get('feature') == 'heating.circuits.0.operating.programs.normalHeating':
                        try:
                            normal_temperature = feature['properties']['temperature']['value']
                            print(f"\nNormal Temperature: {normal_temperature}")
                            continue
                        except (KeyError, TypeError) as e:
                            print(f"Error extracting normal temperature: {e}")
                            continue
                    if feature.get('feature') == 'heating.boiler.sensors.temperature.commonSupply':
                        try:
                            vorlauf_temperature = feature['properties']['value']['value']
                            print(f"\nVorlauf Temperature: {vorlauf_temperature}")
                            continue
                        except (KeyError, TypeError) as e:
                            print(f"Error extracting vorlauf temperature: {e}")
                            continue
                    if feature.get('feature') == 'heating.secondaryCircuit.sensors.temperature.supply':
                        try:
                            vorlauf_secondary_temperature = feature['properties']['value']['value']
                            print(f"\nVorlauf Secondary Temperature: {vorlauf_secondary_temperature}")
                            continue
                        except (KeyError, TypeError) as e:
                            print(f"Error extracting vorlauf secondary temperature: {e}")
                            continue
                if outside_temperature is None:
                    print("\nWarning: Could not find 'heating.sensors.temperature.outside' feature")
                if curve_slope is None:
                    print("\nWarning: Could not find 'heating.circuits.0.heating.curve' feature")
                if curve_shift is None:
                    print("\nWarning: Could not find 'heating.circuits.0.heating.curve' feature")
                if comfort_temperature is None:
                    print("\nWarning: Could not find 'heating.circuits.0.operating.programs.comfortHeating' feature")
                if normal_temperature is None:
                    print("\nWarning: Could not find 'heating.circuits.0.operating.programs.normalHeating' feature")
                if vorlauf_temperature is None:
                    print("\nWarning: Could not find 'heating.boiler.sensors.temperature.commonSupply' feature")
                if vorlauf_secondary_temperature is None:
                    print("\nWarning: Could not find 'heating.secondaryCircuit.sensors.temperature.supply' feature")
            else:
                print("\nWarning: Response does not contain 'data' array")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

        print("=" * 60)
        print("Updating Google Sheet")
        print("=" * 60)
        print("Authentication")
        
        creds = None
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("google_token.json"):
            creds = Credentials.from_authorized_user_file("google_token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(".config.json", SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("google_token.json", "w") as token:
                token.write(creds.to_json())

        google_sheet_id = client.config.get('google_sheet_id')
        service = build("sheets", "v4", credentials=creds)
        

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=google_sheet_id, range="'Messungen'!A2:K")
            .execute()
        )
        values = result.get("values", [])
        print(f"rows found: {len(values)}")
        
        # Prepare new row data with current date/time and sensor values
        berlin_tz = pytz.timezone('Europe/Berlin')
        now = datetime.now(berlin_tz)
        current_date = now.strftime('%d.%m.%Y')
        current_time = now.strftime('%H:%M:%S')
        
        new_row = [
            current_date,
            current_time,
            outside_temperature if outside_temperature is not None else '',
            comfort_temperature if comfort_temperature is not None else '',
            normal_temperature if normal_temperature is not None else '',
            curve_slope if curve_slope is not None else '',
            curve_shift if curve_shift is not None else '',
            vorlauf_temperature if vorlauf_temperature is not None else '',
            vorlauf_secondary_temperature if vorlauf_secondary_temperature is not None else ''
        ]
        
        print(f"\nInserting new row: {new_row}")
        
        # Insert new row at position 2 (after headers)
        # First, we need to insert a blank row
        insert_request = {
            'requests': [{
                'insertDimension': {
                    'range': {
                        'sheetId': 0,  # Assuming first sheet, adjust if needed
                        'dimension': 'ROWS',
                        'startIndex': 1,  # Row 2 (0-indexed)
                        'endIndex': 2
                    },
                    'inheritFromBefore': False
                }
            }]
        }
        
        sheet.batchUpdate(spreadsheetId=google_sheet_id, body=insert_request).execute()
        print("Row inserted successfully")
        
        # Now update the newly inserted row with our data
        update_range = "'Messungen'!A2:I2"
        update_body = {
            'values': [new_row]
        }
        
        sheet.values().update(
            spreadsheetId=google_sheet_id,
            range=update_range,
            valueInputOption='RAW',
            body=update_body
        ).execute()
        
        print(f"Data written to row 2 successfully")
        print(f"Date: {current_date}, Time: {current_time}")


    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
