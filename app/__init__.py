from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate, upgrade
from dotenv import load_dotenv
import os
from sqlalchemy import inspect

load_dotenv()  # load .env

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "devkey")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

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

    # --- DB check / auto-migrate ---
    with app.app_context():
        inspector = inspect(db.engine)
        required_tables = ["users", "customers", "activities"]
        missing_tables = [t for t in required_tables if not inspector.has_table(t)]
        if missing_tables:
            print(f"Missing tables detected: {missing_tables}. Running migrations...")
            upgrade()
        else:
            print("All required tables exist.")

    return app
