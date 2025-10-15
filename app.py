from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel

from db_utils import get_auth_engine, get_user_session

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
babel = Babel()

# Auth session (moved here to avoid circular import)
auth_engine = get_auth_engine()
auth_session = get_user_session(auth_engine)

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    babel.init_app(app)

    # Import blueprints here to avoid circular import
    from auth import auth_bp
    app.register_blueprint(auth_bp)

    return app

# Only for local dev
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=True)
