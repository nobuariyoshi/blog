from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, abort
from flask_bootstrap import Bootstrap5
from functools import wraps
from datetime import datetime
import os
import smtplib
from werkzeug.security import generate_password_hash, check_password_hash
from form import ContactForm, RegisterForm, LoginForm, TravelInsuranceForm, HospitalForm, CreatePostForm, CommentForm
from dotenv import load_dotenv, find_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_ckeditor import CKEditor, CKEditorField
from database import User, Contact, TravelInsurance, Hospital, db, DATABASE_URL, BlogPost, Comment  # Importing from database.py
from flask_migrate import Migrate

# Load environment variables
_ = load_dotenv(find_dotenv())

# Database and Flask-Login configuration
app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
ckeditor = CKEditor(app)
bootstrap = Bootstrap5(app)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL  # Using DATABASE_URL

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Email configuration
MY_EMAIL = os.environ["MY_EMAIL"]
MY_EMAIL_PASSWORD = os.environ["GOOGLE_APP_PASSWORD"]

# Initialize Flask-Migrate
migrate = Migrate(app, db)


def send_email(name, email, phone, message):
    email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(MY_EMAIL, MY_EMAIL_PASSWORD)
        connection.sendmail(MY_EMAIL, MY_EMAIL, email_message)


# Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


@app.context_processor
def inject_user():
    year = datetime.now().year  # Get the current year
    return dict(logged_in=current_user.is_authenticated, year=year)


@app.route("/")
def home():
    latest_posts = BlogPost.query.order_by(BlogPost.id.desc()).limit(3).all()  # Fetch the 3 latest posts
    return render_template("index.html", latest_posts=latest_posts)


# <-------------------------------BLOG------------------------------------>

@app.route("/blog/")
def get_blog():
    # Fetch all blog posts from the database along with their authors
    posts_with_authors = db.session.query(BlogPost, User.first_name, User.last_name).join(User,
                                                                                          BlogPost.author_id == User.id).all()
    # Prepare posts data including author names for the template
    posts_data = [{
        'post': post,
        'author_first_name': first_name,
        'author_last_name': last_name
    } for post, first_name, last_name in posts_with_authors]
    return render_template("blog.html", all_posts=posts_data)


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    # Fetch the requested blog post from the database along with the author's details
    post_with_author = db.session.query(BlogPost, User.first_name, User.last_name).join(User,
                                                                                        BlogPost.author_id == User.id).filter(
        BlogPost.id == post_id).first()
    if not post_with_author:
        return "Post not found", 404
    # Unpack the post and author details
    post, author_first_name, author_last_name = post_with_author
    # Create a CommentForm instance
    comment_form = CommentForm()

    if comment_form.validate_on_submit():
        # Create a new Comment object and save it to the database
        new_comment = Comment(
            text=comment_form.comment_text.data,
            author_id=current_user.id,  # Assuming you have a current user
            post_id=post.id
        )
        db.session.add(new_comment)
        db.session.commit()

    # Fetch comments associated with the blog post
    comments = Comment.query.filter_by(post_id=post.id).all()

    # Prepare post and author data for the template
    post_data = {
        'post': post,
        'author_first_name': author_first_name,
        'author_last_name': author_last_name
    }

    return render_template("post.html", post=post, post_data=post_data, form=comment_form, comments=comments)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,  # Assuming this fetches the correct user ID
            date=datetime.date.today().strftime("%B %d, %Y")
        )
        try:
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for("get_blog"))
        except Exception as e:
            db.session.rollback()  # Rollback the session to a clean state
            print(f"Error adding new post: {e}")
            flash("投稿の追加中にエラーが発生しました。もう一度お試しください。")
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        try:
            post.title = edit_form.title.data
            post.subtitle = edit_form.subtitle.data
            post.img_url = edit_form.img_url.data
            post.author = edit_form.author.data
            post.body = edit_form.body.data

            with db.session.begin():
                db.session.merge(post)

            return redirect(url_for("show_post", post_id=post.id))
        except Exception as e:
            print(f"Error editing post: {e}")
            flash("投稿の修正中にエラーが発生しました。もう一度お試しください。")

    return render_template("make-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    try:
        with db.session.begin():
            db.session.delete(post_to_delete)
        return redirect(url_for('get_blog'))
    except Exception as e:
        print(f"Error deleting post: {e}")
        flash("投稿の削除中にエラーが発生しました。もう一度お試しください。")
        return redirect(url_for('get_blog'))


# <-------------------------------ABOUT------------------------------------>

@app.route("/about")
def about():
    return render_template("about.html")


# Nobu's profile page
@app.route("/about/nobu")
def about_nobu():
    # Additional logic or data fetching can be added here
    return render_template("nobu.html")


# Aoi's profile page
@app.route("/about/aoi")
def about_aoi():
    # Additional logic or data fetching can be added here
    return render_template("aoi.html")


# Takenobu's profile page
@app.route("/about/takenobu")
def about_takenobu():
    # Additional logic or data fetching can be added here
    return render_template("takenobu.html")


# <-------------------------------CONTACT------------------------------------>
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

        flash('メッセージを送信しました！')
        send_email(form.name.data, form.email.data, form.phone.data, form.message.data)
        return redirect(url_for('contact'))

    return render_template("contact.html", form=form)


# <-------------------------------USER AUTHENTICATION------------------------------------>
# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Registration route
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash("既にログインしています。")
        return redirect(url_for('logged_in'))  # Or any other appropriate route
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.email == form.email.data) | (User.username == form.username.data)).first()
        if existing_user:
            flash('そのメールアドレスまたはユーザー名のユーザーは既に存在します。')
            return redirect(url_for('login'))

        # Create a new User instance with first name and last name
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('登録が成功しました！')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("既にログインしています。")
        return redirect(url_for('logged_in'))  # Redirects to a page indicating the user is logged in
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # Verify the password
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('logged_in'))  # Or any other appropriate route after login
        else:
            flash('ユーザー名またはパスワードが無効です')
    return render_template('login.html', form=form)


@app.route('/logged_in')
@login_required
def logged_in():
    # This route displays the "You are logged in" message
    return render_template("logged_in.html")


# Secrets page route
@app.route('/secrets')
@login_required
def secrets():
    return render_template("secrets.html", name=current_user.first_name, logged_in=True)


# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# Modified download route
@app.route('/download/cheatsheet')
@login_required
def download_cheatsheet():
    return send_from_directory('static', path="files/cheat_sheet.pdf")


# <-------------------------------SECRET------------------------------------>
@app.route('/download')
def download():
    return send_from_directory('static', path="files/cheat_sheet.pdf")


# <-------------------------------RESOURCE------------------------------------>
@app.route("/resource")
def resource():
    return render_template("resource.html")


# <-------------------------------TRAVEL INSURANCE------------------------------------>
@app.route("/insurance_companies")
def insurance_companies():
    insurance_companies = TravelInsurance.query.all()
    return render_template('insurance_companies.html', insurance_companies=insurance_companies)


@app.route('/add_insurance_company', methods=["GET", "POST"])
@admin_only
def add_insurance_company():
    form = TravelInsuranceForm()
    if form.validate_on_submit():
        try:
            new_insurance_company = TravelInsurance(
                company=form.company.data,
                premium=form.premium.data,
                medical_expenses=form.medical_expenses.data,
                disease_death=form.disease_death.data,
                age_condition=form.age_condition.data
            )
            with db.session.begin():
                db.session.add(new_insurance_company)

            return redirect(url_for('insurance_companies'))
        except Exception as e:
            print(f"Error adding insurance company: {e}")
            flash("An error occurred while adding the insurance company. Please try again.")

    return render_template('add_insurance_company.html', form=form)


@app.route("/insurance_companies/all-insurance-companies")
def get_all_insurance_companies():
    try:
        result = db.session.query(TravelInsurance).order_by(TravelInsurance.company).all()
        if result:
            # Consider implementing pagination here if the dataset is large
            insurance_companies_list = [insurance_company.to_dict() for insurance_company in result]
            return jsonify(insurance_companies=insurance_companies_list)
        else:
            return jsonify(message="No insurance companies found"), 404
    except Exception as e:
        return jsonify(error=str(e)), 500


# <-------------------------------HOSPITAL------------------------------------>
@app.route("/hospital")
def hospital():
    hospitals = Hospital.query.all()
    return render_template("hospital.html", hospitals=hospitals)


@app.route('/add_hospital', methods=["GET", "POST"])
@admin_only
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


@app.route("/hospitals/search-by-location")
def get_hospital_at_location():
    query_location = request.args.get("loc")
    if not query_location:
        return jsonify(error="Location parameter 'loc' is required."), 400

    try:
        result = db.session.query(Hospital).filter(Hospital.location == query_location).all()
        if result:
            hospitals_list = [hospital.to_dict() for hospital in result]
            return jsonify(hospitals=hospitals_list)
        else:
            return jsonify(error="No hospitals found at the specified location."), 404
    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False)
