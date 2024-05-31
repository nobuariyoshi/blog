from flask import Flask
from dotenv import load_dotenv, find_dotenv
from database import db, User, DATABASE_URL
from werkzeug.security import generate_password_hash
import os

# Load environment variables
load_dotenv(find_dotenv())

# Database configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

with app.app_context():
    # Create all the tables
    db.create_all()

    # Create the first user
    username = os.getenv("ADMIN")  # Username from the .env file
    email = os.getenv("MY_EMAIL")
    first_name = os.getenv("FIRST_NAME")  # First name from the .env file
    last_name = os.getenv("LAST_NAME")  # Last name from the .env file
    password = os.getenv("LOGIN_PASSWORD")  # Password from the .env file

    # Check if the user already exists
    existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
    if existing_user:
        print("User already exists.")
    else:
        # Create and add the new user to the database
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        print("Admin user created successfully.")
