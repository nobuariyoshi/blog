from dotenv import load_dotenv
import logging
import requests
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(os.path.expanduser('~/config/.env'))

# Email configuration
my_email = os.environ["MY_EMAIL"]
client_id = os.environ['CLIENT_365_ID']
client_secret = os.environ['CLIENT_365_SECRET']
tenant_id = os.environ['TENANT_365_ID']
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

def get_access_token(refresh_token):
    payload = {
        'client_id': client_id,
        'scope': 'offline_access Mail.ReadWrite Mail.send',
        'grant_type': 'refresh_token',
        'client_secret': client_secret,
        'refresh_token': refresh_token
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        response = requests.post(token_url, headers=headers, data=payload)
        response.raise_for_status()  # Check for request's success
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.exception("An error occurred while requesting the token")
        return None

def send_message_email(name, email, message):
    refresh_token = os.environ['REFRESH_TOKEN']
    tokens = get_access_token(refresh_token)
    if tokens is None:
        logger.error("Failed to obtain access token.")
        return False

    access_token = tokens.get('access_token')
    if not access_token:
        logger.error("No access token found in the response.")
        return False

    html_content = f"""
    <html>
    <body>
        <p>Name: {name}</p>
        <p>Email: {email}</p>
        <p>Message: {message}</p>
    </body>
    </html>
    """

    request_body = {
        'message': {
            'toRecipients': [
                {
                    'emailAddress': {
                        'address': my_email
                    }
                }
            ],
            'subject': f"New Contact Form Submission from {name}",
            "body": {
                "contentType": "html",
                "content": html_content
            },
            'importance': 'normal',
        }
    }

    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    GRAPH_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    endpoint = GRAPH_ENDPOINT + '/me/sendMail'

    try:
        response = requests.post(endpoint, headers=headers, json=request_body)
        response.raise_for_status()  # Raise an exception if request fails

        if response.status_code == 202:
            logger.info(f"Email sent to: {my_email}")
            return True
        else:
            logger.exception(f"Email not sent to: {my_email}")
            return False

    except requests.exceptions.RequestException as e:
        logger.exception("An error occurred while sending the email")
        return False
