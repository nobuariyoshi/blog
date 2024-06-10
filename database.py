from sqlalchemy import ForeignKey, Integer, String, Text, Boolean, DateTime, Column
from sqlalchemy.orm import declarative_base, relationship
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.expanduser('~/config/.env'))

# Get password from environment variable
mysql_password = os.environ.get('MYSQL_PASSWORD')
if not mysql_password:
    raise ValueError("MYSQL_PASSWORD environment variable is not set.")

# Get other environment variables
mysql_user = os.environ.get('MYSQL_USER', 'root')
mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
mysql_db = os.environ.get('MYSQL_DB', 'telemedicine')

# Setup the database connection
DATABASE_URL = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"

# Define the declarative base
Base = declarative_base()

# Initialize SQLAlchemy with the base model
db = SQLAlchemy(model_class=Base)


# Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    password = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('BlogPost', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='comment_author', lazy=True, overlaps="user_comments,comments")

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
    date = Column(DateTime, default=datetime.utcnow)
    last_edited = Column(DateTime, nullable=True)  # New field for last edited date
    body = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    img_url = Column(String(500), nullable=True)
    comments = relationship('Comment', backref='post_comments', lazy=True, cascade="all, delete-orphan",
                            overlaps="comments,post_comments")
    draft = Column(Boolean, default=True)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id', ondelete='CASCADE'), nullable=False)

    author = db.relationship('User', backref=db.backref('user_comments', lazy=True, cascade="all, delete-orphan",
                                                        overlaps="comment_author,comments"))
    post = db.relationship('BlogPost', backref=db.backref('post_comments', lazy=True, cascade="all, delete-orphan",
                                                          overlaps="comments,post_comments"))
