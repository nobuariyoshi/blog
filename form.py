from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, URLField, BooleanField
from flask_ckeditor import CKEditor, CKEditorField
from wtforms.validators import DataRequired, Email, Length, EqualTo, URL


class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone')
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Submit')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=50)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])  # New
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])  # New
    password = PasswordField('Password', validators=[DataRequired(), Length(min=15)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')  # Adding the remember me checkbox
    submit = SubmitField('Login')



class TravelInsuranceForm(FlaskForm):
    company = StringField('保険会社', validators=[DataRequired()])
    premium = StringField('保険料', validators=[DataRequired()])
    medical_expenses = StringField('治療費用', validators=[DataRequired()])
    disease_death = StringField('疾病死亡', validators=[DataRequired()])
    age_condition = StringField('年齢条件', validators=[DataRequired()])
    submit = SubmitField('Submit')


class HospitalForm(FlaskForm):
    name = StringField('Hospital Name', validators=[DataRequired()])
    address = StringField('Address')
    phone = StringField('Phone Number')
    url = URLField('Website URL')  # Add a URL field
    description = TextAreaField('Description')
    submit = SubmitField('Add Hospital')


class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")

