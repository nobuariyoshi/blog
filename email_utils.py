from dotenv import load_dotenv, find_dotenv
import logging
import requests
import ast
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
_ = load_dotenv(find_dotenv())

# Email configuration
my_email = os.environ["MY_EMAIL"]
client_id = os.environ['CLIENT_365_ID']
client_secret = os.environ['CLIENT_365_SECRET']
tenant_id = os.environ['TENANT_365_ID']
refresh_token = os.environ['REFRESH_TOKEN']
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

# Create payload using environmental variables
payload = {
    'client_id': client_id,
    'scope': 'offline_access Mail.ReadWrite Mail.send',
    'grant_type': 'refresh_token',
    'client_secret': client_secret,
    'refresh_token': refresh_token
}

# Set headers
headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

try:
    # Send the request with dynamic payload
    response = requests.post(token_url, headers=headers, data=payload)
    response.raise_for_status()  # Check for request's success

    # Convert string response to dictionary
    result = ast.literal_eval(response.text)

except requests.exceptions.RequestException as e:
    logger.exception("An error occurred while requesting the token")


def send_message_email(name, email, phone, message):
    # Format the email content with user's details
    mail_text = f"Name: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}"
    html_content = f"""
    <html>
    <body>
        <p>Name: {name}</p>
        <p>Email: {email}</p>
        <p>Phone: {phone}</p>
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
        'Authorization': 'Bearer ' + result['access_token']
    }

    GRAPH_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    endpoint = GRAPH_ENDPOINT + '/me/sendMail'

    try:
        response = requests.post(endpoint, headers=headers, json=request_body)
        response.raise_for_status()  # Raise an exception if request fails

        if response.status_code == 202:
            logger.info(f"Email sent to: {my_email}")
        else:
            logger.exception(f"Email not sent to: {my_email}")

    except requests.exceptions.RequestException as e:
        logger.exception("An error occurred while sending the email")
    return True


def send_chat_email(chat):
    # Format the email content with chat content
    html_content = f"""
    <html>
    <body>
        <p>Chat:</p>
        <p>{chat}</p>
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
            "body": {
                "contentType": "html",
                "content": html_content
            },
            'importance': 'normal',
        }
    }

    headers = {
        'Authorization': 'Bearer ' + result['access_token']
    }

    GRAPH_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    endpoint = GRAPH_ENDPOINT + '/me/sendMail'

    try:
        response = requests.post(endpoint, headers=headers, json=request_body)
        response.raise_for_status()  # Raise an exception if request fails

        if response.status_code == 202:
            logger.info(f"Email sent to: {my_email} regarding chat content.")
        else:
            logger.exception(f"Email not sent to: {my_email}")

    except requests.exceptions.RequestException as e:
        logger.exception("An error occurred while sending the email")
    return True
