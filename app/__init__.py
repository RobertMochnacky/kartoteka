from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate, upgrade
from dotenv import load_dotenv
import os
from sqlalchemy import inspect
from flask_babel import Babel
import click

load_dotenv()  # load .env

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
migrate = Migrate()
babel = Babel()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "devkey")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'sk']  # English and Slovak

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app, default_locale="en", default_timezone="Europe/Bratislava")

    # Import models here to avoid circular imports
    from .models import User, Customer, Activity

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Blueprints
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from .main import main_bp
    app.register_blueprint(main_bp)

    # Optional: Register translation CLI commands
    register_translation_commands(app)

    return app

def register_translation_commands(app):
    @app.cli.group()
    def translate():
        """Translation and localization commands"""
        pass

    @translate.command()
    @click.option('--lang', default='sk', help='Language code (default: sk)')
    def init(lang):
        """Initialize new translation"""
        os.system(f"pybabel init -i messages.pot -d translations -l {lang}")

    @translate.command()
    def update():
        """Update translation template"""
        os.system("pybabel update -i messages.pot -d translations")

    @translate.command()
    def compile():
        """Compile translations"""
        os.system("pybabel compile -d translations")
