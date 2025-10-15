from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel

from db_utils import get_auth_engine, get_user_session

# ---------------------------
# Extensions
# ---------------------------
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
babel = Babel()

# ---------------------------
# Auth session
# ---------------------------
auth_engine = get_auth_engine()
auth_session = get_user_session(auth_engine)

# ---------------------------
# Factory function
# ---------------------------
def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    babel.init_app(app)

    # Import blueprints here to avoid circular import
    from auth import auth_bp
    app.register_blueprint(auth_bp)

    # Optionally, import other blueprints here
    # from views import main_bp
    # app.register_blueprint(main_bp)

    return app

# ---------------------------
# Optional local run
# ---------------------------
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
