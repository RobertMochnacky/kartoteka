import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Auth DB
    AUTH_DATABASE_URI = os.getenv("AUTH_DATABASE_URL", "sqlite:///auth.db")

    # Babel
    BABEL_DEFAULT_LOCALE = os.getenv("BABEL_DEFAULT_LOCALE", "en")
