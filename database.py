from sqlalchemy import ForeignKey, Integer, String, Text, Boolean, DateTime, Column
from sqlalchemy.orm import declarative_base, relationship
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv

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
    first_name = Column(String(50))  # New
    last_name = Column(String(50))  # New
    password = Column(String(256))
    created_at = Column(DateTime, default=datetime.utcnow)
    # Add a relationship to BlogPost
    posts = relationship('BlogPost', backref='author', lazy=True)
    # Add a relationship to Comment
    comments = relationship('Comment', backref='author', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Contact(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id = Column(Integer, primary_key=True)
    title = Column(String(250), unique=True, nullable=False)
    subtitle = Column(String(250), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)  # Changed to DateTime, defaults to current time
    body = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # ForeignKey to reference User
    img_url = Column(String(500), nullable=False)
    comments = relationship('Comment', backref='post', lazy=True,
                            cascade="all, delete-orphan")  # Relationship to Comment
    draft = Column(Boolean, default=True)  # New column to indicate draft status, defaulting to True


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(Text, nullable=False)
    date_posted = db.Column(DateTime, default=datetime.utcnow, nullable=False)
    author_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)  # Add ForeignKey to reference User
    post_id = db.Column(db.Integer, ForeignKey('blog_posts.id', ondelete='CASCADE'),
                        nullable=False)  # Add ForeignKey to reference BlogPost
