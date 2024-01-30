import os
import smtplib
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

MY_EMAIL = os.environ["MY_EMAIL"]
MY_EMAIL_PASSWORD = os.environ["GOOGLE_APP_PASSWORD"]

def send_email():
    email_message = "hello"
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(MY_EMAIL, MY_EMAIL_PASSWORD)
        connection.sendmail(MY_EMAIL, MY_EMAIL, email_message)

send_email()