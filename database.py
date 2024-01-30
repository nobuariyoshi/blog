from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Integer, String, Column, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship

# Load environment variables
load_dotenv()

# Get password from environment variable
postgresql_password = os.environ.get('POSTGRESQL_PASSWORD')
if not postgresql_password:
    raise ValueError("POSTGRESQL_PASSWORD environment variable is not set.")

# Setup the database connection
DATABASE_URL = f"postgresql://postgres:{postgresql_password}@localhost/telemedicine"

# Define the declarative base
Base = declarative_base()

# Initialize SQLAlchemy with the base model
db = SQLAlchemy(model_class=Base)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(25), unique=True, nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Contact(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TravelInsurance(db.Model):
    __tablename__ = 'travel_insurances'

    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(120), nullable=False)
    premium = db.Column(db.String(120), nullable=False)
    medical_expenses = db.Column(db.String(120), nullable=False)
    disease_death = db.Column(db.String(120), nullable=False)
    age_condition = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Uncomment the next line if TravelInsurance is related to a User
    # user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)


class Hospital(db.Model):
    __tablename__ = 'hospitals'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(120))
    url = db.Column(db.String(255))  # Add a URL column
    description = db.Column(db.Text)
    # Add other fields as needed
