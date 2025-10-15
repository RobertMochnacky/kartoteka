from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect
import os

# --- Extensions ---
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
babel = Babel()
csrf = CSRFProtect()

# --- App Factory ---
def create_app():
    app = Flask(__name__)

    # --- Configuration ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 'postgresql://user:password@db/auth_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- Initialize extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    babel.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'

    # --- Import models ---
    from models import User

    # --- User loader for Flask-Login ---
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Blueprints ---
    from auth import auth_bp
    from routes import main_bp  # if you have a routes.py for general pages

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app


# --- Create app for Gunicorn ---
app = create_app()
