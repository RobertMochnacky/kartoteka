from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register")

class ClientForm(FlaskForm):
    name = StringField("Client name", validators=[DataRequired()])
    contact = StringField("Contact info")
    notes = TextAreaField("Notes")
    submit = SubmitField("Save Client")

class ActivityForm(FlaskForm):
    activity_date = DateField("Activity date", validators=[DataRequired()], format="%Y-%m-%d")
    person_name = StringField("Person responsible")
    description = TextAreaField("Task description", validators=[DataRequired()])
    submit = SubmitField("Add Activity")
