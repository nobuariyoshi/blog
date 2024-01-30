from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, URLField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone')
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Submit')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
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

