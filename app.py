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

# Config
AUTH_DB_URL = "postgresql://postgres:postgres@db:5432/authdb"
auth_engine = get_auth_engine(AUTH_DB_URL)
SessionAuth = sessionmaker(bind=auth_engine)
auth_session = SessionAuth()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.register_blueprint(auth_bp, url_prefix="/auth")

# Babel setup
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'sk']
babel = Babel(app)

@babel.localeselector
def get_locale():
    lang = request.args.get('lang')
    if lang in app.config['BABEL_SUPPORTED_LOCALES']:
        return lang
    return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])

# Login manager
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return auth_session.query(AuthUser).get(int(user_id))

# Dynamic user DB session
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
