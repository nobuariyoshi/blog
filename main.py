from post import Post
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
import datetime
import os
import smtplib
from werkzeug.security import check_password_hash
from form import ContactForm, RegisterForm, LoginForm, TravelInsuranceForm, HospitalForm
from dotenv import load_dotenv, find_dotenv
import csv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import User, Contact, TravelInsurance, Hospital, db, DATABASE_URL  # Importing from database.py

# Load environment variables
_ = load_dotenv(find_dotenv())

# Database and Flask-Login configuration
app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
bootstrap = Bootstrap5(app)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL  # Using DATABASE_URL
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Email configuration
MY_EMAIL = os.environ["MY_EMAIL"]
MY_EMAIL_PASSWORD = os.environ["GOOGLE_APP_PASSWORD"]

# Fetch and create post objects
posts = requests.get("https://api.npoint.io/c790b4d5cab58020d391").json()
post_objects = [Post(post["id"], post["title"], post["subtitle"], post["body"]) for post in posts]


def send_email(name, email, phone, message):
    email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(MY_EMAIL, MY_EMAIL_PASSWORD)
        connection.sendmail(MY_EMAIL, MY_EMAIL, email_message)


@app.route("/")
def home():
    year = datetime.datetime.now().year
    return render_template("index.html", year=year, all_posts=post_objects)


@app.route("/blog/")
def get_blog():
    return render_template("blog.html", all_posts=post_objects)


@app.route("/post/<int:index>")
def show_post(index):
    requested_post = next((post for post in post_objects if post.id == index), None)
    return render_template("post.html", post=requested_post)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        new_contact = Contact(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            message=form.message.data
        )
        db.session.add(new_contact)
        db.session.commit()

        flash('Successfully sent your message!')
        send_email(form.name.data, form.email.data, form.phone.data, form.message.data)
        return redirect(url_for('contact'))

    return render_template("contact.html", form=form)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Your existing functions and routes...

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/resource")
def resource():
    return render_template("resource.html")


@app.route("/insurance_companies")
def insurance_companies():
    insurance_companies = TravelInsurance.query.all()
    return render_template('insurance_companies.html', insurance_companies=insurance_companies)


@app.route('/add_insurance_company', methods=["GET", "POST"])
def add_insurance_company():
    form = TravelInsuranceForm()
    if form.validate_on_submit():
        new_insurance_company = TravelInsurance(
            company=form.company.data,
            premium=form.premium.data,
            medical_expenses=form.medical_expenses.data,
            disease_death=form.disease_death.data,
            age_condition=form.age_condition.data
        )
        db.session.add(new_insurance_company)
        db.session.commit()

        return redirect(url_for('insurance_companies'))

    return render_template('add_insurance_company.html', form=form)


@app.route("/hospital")
def hospital():
    hospitals = Hospital.query.all()
    return render_template("hospital.html", hospitals=hospitals)


@app.route('/add_hospital', methods=["GET", "POST"])
def add_hospital():
    form = HospitalForm()
    if form.validate_on_submit():
        new_hospital = Hospital(
            name=form.name.data,
            address=form.address.data,
            phone=form.phone.data,
            url=form.url.data,  # Save the URL
            description=form.description.data
        )
        db.session.add(new_hospital)
        db.session.commit()

        flash('New hospital added successfully!')
        return redirect(url_for('hospital'))

    return render_template('add_hospital.html', form=form)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
