from flask import Flask
from config import Config
from flask_migrate import Migrate
from flask_login import LoginManager
from models import db, User
from auth import auth_bp
from routes import routes_bp
import os

login_manager = LoginManager()
login_manager.login_view = "auth.login"  # redirect to login page if not logged in

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "super-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    Migrate(app, db)

    # Initialize login manager
    login_manager.init_app(app)

    from auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from main import main_bp
    app.register_blueprint(main_bp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
