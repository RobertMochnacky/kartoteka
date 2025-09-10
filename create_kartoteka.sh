#!/bin/bash

# Project folder
PROJECT="flask_client_activity_app"
rm -rf $PROJECT
mkdir -p $PROJECT/templates
mkdir -p $PROJECT/static

echo "Creating files..."

# -----------------------------
# 1. requirements.txt
# -----------------------------
cat > $PROJECT/requirements.txt <<EOL
Flask==2.3.4
Flask-WTF==1.1.1
WTForms==3.0.1
SQLAlchemy==2.0.20
Flask-Login==0.6.3
psycopg2-binary==2.9.9
Flask-Migrate==4.0.4
gunicorn==21.2.0
python-dotenv==1.0.0
Flask-Babel==3.1.1
EOL

# -----------------------------
# 2. models_auth.py
# -----------------------------
cat > $PROJECT/models_auth.py <<'EOL'
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

class AuthUser(UserMixin, Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), default="user")
    db_name = Column(String(64), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "admin"
EOL

# -----------------------------
# 3. models_user.py
# -----------------------------
cat > $PROJECT/models_user.py <<'EOL'
from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    contact = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    activities = relationship("Activity", backref="client", cascade="all, delete-orphan")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    activity_date = Column(Date, nullable=False)
    person_name = Column(String(255))
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
EOL

# -----------------------------
# 4. db_utils.py
# -----------------------------
cat > $PROJECT/db_utils.py <<'EOL'
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models_user import Base as UserBase
import psycopg2

def create_user_db(user_db_name, db_url="postgresql://postgres:postgres@db:5432/postgres"):
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f'CREATE DATABASE {user_db_name}')
    cur.close()
    conn.close()

def init_user_db(user_db_url):
    engine = create_engine(user_db_url)
    UserBase.metadata.create_all(engine)

def get_user_session(user_db_url):
    engine = create_engine(user_db_url)
    Session = scoped_session(sessionmaker(bind=engine))
    return Session

def get_auth_engine(auth_db_url):
    from models_auth import Base
    engine = create_engine(auth_db_url)
    Base.metadata.create_all(engine)
    return engine
EOL

# -----------------------------
# 5. forms.py
# -----------------------------
cat > $PROJECT/forms.py <<'EOL'
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
EOL

# -----------------------------
# 6. app.py
# -----------------------------
cat > $PROJECT/app.py <<'EOL'
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_required, current_user
from flask_babel import Babel, gettext as _
from models_user import Client, Activity
from forms import ClientForm, ActivityForm
from db_utils import get_user_session, get_auth_engine
from models_auth import AuthUser
from auth import auth_bp
from sqlalchemy.orm import sessionmaker
import os

AUTH_DB_URL = "postgresql://postgres:postgres@db:5432/authdb"
auth_engine = get_auth_engine(AUTH_DB_URL)
SessionAuth = sessionmaker(bind=auth_engine)
auth_session = SessionAuth()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.register_blueprint(auth_bp, url_prefix="/auth")

app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'sk']
babel = Babel(app)

@babel.localeselector
def get_locale():
    lang = request.args.get('lang')
    if lang in app.config['BABEL_SUPPORTED_LOCALES']:
        return lang
    return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return auth_session.query(AuthUser).get(int(user_id))

def get_user_db():
    return get_user_session(f"postgresql://postgres:postgres@db:5432/{current_user.db_name}")

@app.route("/")
def index():
    return redirect(url_for("list_clients"))

@app.route("/clients")
@login_required
def list_clients():
    session = get_user_db()
    clients = session.query(Client).order_by(Client.created_at.desc()).all()
    return render_template("clients.html", clients=clients, _=_)

@app.route("/clients/new", methods=["GET","POST"])
@login_required
def new_client():
    form = ClientForm()
    if form.validate_on_submit():
        session = get_user_db()
        client = Client(name=form.name.data.strip(),
                        contact=form.contact.data.strip(),
                        notes=form.notes.data.strip())
        session.add(client)
        session.commit()
        flash(_("Client added"), "success")
        return redirect(url_for("list_clients"))
    return render_template("new_client.html", form=form, _=_)

@app.route("/clients/<int:client_id>", methods=["GET","POST"])
@login_required
def client_detail(client_id):
    session = get_user_db()
    client = session.query(Client).get(client_id)
    if not client:
        flash(_("Client not found"), "error")
        return redirect(url_for("list_clients"))
    form = ActivityForm()
    if form.validate_on_submit():
        act = Activity(client_id=client.id,
                       activity_date=form.activity_date.data,
                       person_name=form.person_name.data.strip(),
                       description=form.description.data.strip())
        session.add(act)
        session.commit()
        flash(_("Activity added"), "success")
        return redirect(url_for("client_detail", client_id=client.id))
    activities = client.activities
    return render_template("client_detail.html", client=client, activities=activities, form=form, _=_)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
EOL

# -----------------------------
# 7. Templates
# -----------------------------

# base.html
cat > $PROJECT/templates/base.html <<'EOL'
<!doctype html>
<html>
<head>
  <title>Client Activity Tracker</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
<nav>
  <a href="{{ url_for('list_clients') }}">{{ _("Clients") }}</a>
  <a href="{{ url_for('new_client') }}">{{ _("New Client") }}</a>
  {% if current_user.is_authenticated %}
      {% if current_user.is_admin() %}
        <a href="{{ url_for('auth.list_users') }}">{{ _("Admin Panel") }}</a>
      {% endif %}
      <a href="{{ url_for('auth.logout') }}">{{ _("Logout") }}</a>
  {% else %}
      <a href="{{ url_for('auth.login') }}">{{ _("Login") }}</a>
  {% endif %}
</nav>

<div class="lang-switcher">
  {{ _("Language") }}:
  <a href="?lang=en">English</a> | <a href="?lang=sk">Slovensky</a>
</div>

{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <ul class="flashes">
    {% for category, message in messages %}
      <li class="{{ category }}">{{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}

<div class="content">
{% block content %}{% endblock %}
</div>
</body>
</html>
EOL

# Other templates (login.html, register.html, clients.html, new_client.html, client_detail.html, admin_users.html, admin_reset_password.html)
# Add these templates similarly to base.html using the content we prepared earlier

# style.css
cat > $PROJECT/static/style.css <<'EOL'
body { font-family: Arial, sans-serif; margin: 20px; }
nav a { margin-right: 10px; text-decoration: none; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
table, th, td { border: 1px solid #ccc; }
th, td { padding: 8px; text-align: left; }
.flashes li { list-style-type: none; margin: 5px 0; }
.flashes .success { color: green; }
.flashes .error { color: red; }
.flashes .info { color: blue; }
form p { margin-bottom: 10px; }
EOL

# Dockerfile
cat > $PROJECT/Dockerfile <<'EOL'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
EOL

# docker-compose.yml
cat > $PROJECT/docker-compose.yml <<'EOL'
version: "3.9"
services:
  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - pg_data:/var/lib/postgresql/data
  web:
    build: .
    command: gunicorn --bind 0.0.0.0:5000 app:app
    volumes:
      - .:/app
    ports:
      - "5000:5000"
    depends_on:
      - db
volumes:
  pg_data:
EOL

# Zip the project
cd ..
zip -r flask_client_activity_app.zip $PROJECT

echo "Project created and zipped as flask_client_activity_app.zip"
