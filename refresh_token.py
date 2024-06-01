import requests
import os
from dotenv import load_dotenv

load_dotenv()

client_id = os.environ['CLIENT_365_ID']
client_secret = os.environ['CLIENT_365_SECRET']
tenant_id = os.environ['TENANT_365_ID']
redirect_uri = os.environ['REDIRECT_URI']
authorization_code = os.environ['AUTHORIZATION_CODE_RECEIVED']

token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
payload = {
    'client_id': client_id,
    'scope': 'offline_access Mail.ReadWrite Mail.Send',
    'code': authorization_code,
    'redirect_uri': redirect_uri,
    'grant_type': 'authorization_code',
    'client_secret': client_secret,
}

headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

response = requests.post(token_url, headers=headers, data=payload)
response.raise_for_status()  # Ensure the request was successful

tokens = response.json()
access_token = tokens['access_token']
refresh_token = tokens['refresh_token']

print(f"Access Token: {access_token}")
print(f"Refresh Token: {refresh_token}")
