from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, g, send_from_directory
from flask_bootstrap import Bootstrap5
from flask_wtf.csrf import CSRFProtect
from functools import wraps
from datetime import datetime
import os
from O365 import Account, FileSystemTokenBackend
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from form import ContactForm, RegisterForm, LoginForm, CreatePostForm, CommentForm
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_ckeditor import CKEditor, upload_success, upload_fail
from database import User, Contact, db, DATABASE_URL, BlogPost, Comment
from flask_migrate import Migrate
from email.mime.text import MIMEText
from email_utils import send_message_email
import logging
from sqlalchemy.sql import text
import hashlib

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(os.path.expanduser('~/config/.env'))

# Database and Flask-Login configuration
app = Flask(__name__)
csrf = CSRFProtect(app)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
ckeditor = CKEditor(app)
app.config['CKEDITOR_FILE_UPLOADER'] = 'upload'
bootstrap = Bootstrap5(app)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 28000  # Recycle connections every 28000 seconds
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 20  # Timeout for getting a connection from the pool
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure the upload directory exists
def ensure_upload_directory_exists():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'])
            os.chmod(app.config['UPLOAD_FOLDER'], 0o755)
        except Exception as e:
            logger.error(f"Error creating upload directory: {e}")
            raise

ensure_upload_directory_exists()

db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Email configuration
my_email = os.environ["MY_EMAIL"]
client_id = os.environ['CLIENT_365_ID']
client_secret = os.environ['CLIENT_365_SECRET']
tenant_id = os.environ['TENANT_365_ID']
redirect_uri = os.environ['REDIRECT_URI']
token_backend = FileSystemTokenBackend(token_path='.', token_filename='o365_token.txt')
credentials = (client_id, client_secret)

account = Account(credentials, token_backend=token_backend)


# Gravatar function
def gravatar(email, size=100, default='identicon', rating='g'):
    url = 'https://www.gravatar.com/avatar/'
    hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    return f'{url}{hash}?s={size}&d={default}&r={rating}'

app.jinja_env.filters['gravatar'] = gravatar


# Admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_user():
    year = datetime.now().year
    return dict(logged_in=current_user.is_authenticated, year=year)


@app.before_request
def set_mysql_timeout():
    if not hasattr(g, 'mysql_timeout_set'):
        with db.engine.connect() as connection:
            connection.execute(text("SET SESSION wait_timeout = 28800"))
            connection.execute(text("SET SESSION interactive_timeout = 28800"))
        g.mysql_timeout_set = True


@app.route("/")
def home():
    latest_posts = BlogPost.query.order_by(BlogPost.id.desc()).limit(10).all()
    return render_template("index.html", all_posts=latest_posts)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route("/blog")
def get_blog():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    paginated_posts = db.session.query(BlogPost, User.first_name, User.last_name).join(User, BlogPost.author_id == User.id).order_by(BlogPost.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    posts_data = [{
        'post': post,
        'author_first_name': first_name,
        'author_last_name': last_name
    } for post, first_name, last_name in paginated_posts.items]

    next_url = url_for('get_blog', page=paginated_posts.next_num) if paginated_posts.has_next else None
    prev_url = url_for('get_blog', page=paginated_posts.prev_num) if paginated_posts.has_prev else None

    return render_template("blog.html", all_posts=posts_data, next_url=next_url, prev_url=prev_url)


@app.route("/blog/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    post_with_author = db.session.query(BlogPost, User.first_name, User.last_name).join(User, BlogPost.author_id == User.id).filter(BlogPost.id == post_id).first()
    if not post_with_author:
        return "Post not found", 404
    post, author_first_name, author_last_name = post_with_author
    comment_form = CommentForm()
    if comment_form.validate_on_submit() and current_user.is_authenticated:
        new_comment = Comment(
            text=comment_form.comment_text.data,
            author_id=current_user.id,
            post_id=post.id
        )
        db.session.add(new_comment)
        db.session.commit()

        # Send email notification
        send_message_email(
            name=current_user.username,
            email=current_user.email,
            message=f"A new comment was posted by {current_user.username} on the post '{post.title}':\n\n{new_comment.text}"
        )
        flash("Comment posted successfully and email notification sent.")
        return redirect(url_for('show_post', post_id=post.id))

    comments = Comment.query.filter_by(post_id=post.id).all()
    post_data = {
        'post': post,
        'author_first_name': author_first_name,
        'author_last_name': author_last_name
    }
    return render_template("post.html", post=post, post_data=post_data, form=comment_form, comments=comments)


@app.route("/new-post", methods=["GET", "POST"])
@login_required
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=datetime.now()
        )
        try:
            db.session.add(new_post)
            db.session.commit()
            flash("Post added successfully!")
            return redirect(url_for("get_blog"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding new post: {e}")
    else:
        if request.method == "POST":
            print("Form not validated:", form.errors)
    return render_template("make-post.html", form=form)


@app.route("/blog/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = CreatePostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.img_url = form.img_url.data
        post.body = form.body.data
        post.last_edited = datetime.now()  # Update the last edited date
        try:
            db.session.commit()
            return redirect(url_for("show_post", post_id=post.id))
        except Exception as e:
            db.session.rollback()
            print(f"Error editing post: {e}")
            flash("投稿の修正中にエラーが発生しました。もう一度お試しください。")
    return render_template("make-post.html", form=form, is_edit=True, post=post)


@app.route("/blog/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.session.get(BlogPost, post_id)
    if not post_to_delete:
        flash("投稿が見つかりませんでした。")
        return redirect(url_for('get_blog'))
    try:
        db.session.delete(post_to_delete)
        db.session.commit()
        flash("投稿が正常に削除されました。")
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting post: {e}")
        flash("投稿の削除中にエラーが発生しました。もう一度お試しください。")
    return redirect(url_for('get_blog'))


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if request.method == "POST":
        if form.validate_on_submit():
            new_contact = Contact(
                name=form.name.data,
                email=form.email.data,
                message=form.message.data
            )
            db.session.add(new_contact)
            db.session.commit()
            flash('メッセージを送信しました！')
            print(f"Form Data: {form.name.data}, {form.email.data}, {form.message.data}")
            send_message_email(form.name.data, form.email.data, form.message.data)
            print("Email sent successfully!")
            return redirect(url_for('contact_success'))
        else:
            print("Form not validated:", form.errors)
    return render_template("contact.html", msg_sent=False, form=form)


@app.route("/contact/success")
def contact_success():
    form = ContactForm()
    return render_template("contact.html", msg_sent=True, form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash("既にログインしています。")
        return redirect(url_for('logged_in'))
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.email == form.email.data) | (User.username == form.username.data)).first()
        if existing_user:
            flash('そのメールアドレスまたはユーザー名のユーザーは既に存在します。')
            return redirect(url_for('login'))
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


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("既にログインしています。")
        return redirect(url_for('logged_in'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('logged_in'))
        else:
            flash('ユーザー名またはパスワードが無効です')
    return render_template('login.html', form=form)


@app.route('/logged_in')
@login_required
def logged_in():
    return render_template("logged_in.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/start-auth')
def start_auth():
    auth_url, state = account.con.get_authorization_url(
        requested_scopes=['offline_access', 'User.Read', 'Mail.ReadWrite', 'Mail.Send'],
        redirect_uri=redirect_uri
    )
    session['oauth_state'] = state
    return redirect(auth_url)


@app.route('/callback')
def oauth_callback():
    state = session.get('oauth_state')
    code = request.args.get('code')
    if code:
        logger.debug(f"Received OAuth callback with code: {code}")

        credentials = (os.environ['CLIENT_365_ID'], os.environ['CLIENT_365_SECRET'])
        token_backend = FileSystemTokenBackend(token_path='.', token_filename='o365_token.txt')

        # Create the Account instance with the token backend
        account = Account(credentials, token_backend=token_backend)

        if account.authenticate(code=code, redirect_uri=redirect_uri):
            logger.debug("Account is authenticated.")
            flash('You have been successfully authenticated with Microsoft 365.')
            return redirect(url_for('home'))
        else:
            logger.error("Failed to authenticate the account with Microsoft 365.")
            flash('Authentication with Microsoft 365 failed during token exchange.')
            return redirect(url_for('error_page'))
    else:
        logger.error("No authorization code was provided in the OAuth callback.")
        flash('Failed to authenticate with Microsoft 365. No authorization code was provided.')
        return redirect(url_for('home'))


@app.route('/error')
def error_page():
    return render_template('error.html')


# Route to handle file uploads for CKEditor
@app.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('upload')
    if not f:
        return upload_fail('No file uploaded')
    filename = secure_filename(f.filename)
    f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    url = url_for('uploaded_files', filename=filename)
    return upload_success(url)


@app.route('/uploads/<filename>')
def uploaded_files(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
