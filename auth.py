from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models_auth import AuthUser
from forms import LoginForm, RegisterForm
from db_utils import create_user_db, init_user_db
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
from app import auth_session  # session connected to Auth DB

auth_bp = Blueprint("auth", __name__)

def admin_required(f):
    from functools import wraps
    from flask import abort
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated

# LOGIN
@auth_bp.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = auth_session.query(AuthUser).filter_by(username=form.username.data.strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for("app.list_clients"))
        flash("Invalid username or password.", "error")
    return render_template("login.html", form=form)

# LOGOUT
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))

# REGISTER (creates per-user DB)
@auth_bp.route("/register", methods=["GET","POST"])
@login_required
@admin_required
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()
        password = form.password.data.strip()

        if auth_session.query(AuthUser).filter_by(username=username).first():
            flash("Username exists", "error")
            return redirect(url_for("auth.register"))
        if auth_session.query(AuthUser).filter_by(email=email).first():
            flash("Email exists", "error")
            return redirect(url_for("auth.register"))

        db_name = f"clientdb_{username}"
        # 1. Create user DB
        create_user_db(db_name)
        # 2. Initialize tables
        user_db_url = f"postgresql://postgres:postgres@db:5432/{db_name}"
        init_user_db(user_db_url)
        # 3. Save in Auth DB
        user = AuthUser(username=username, email=email, role="user", db_name=db_name)
        user.set_password(password)
        auth_session.add(user)
        auth_session.commit()
        flash(f"User {username} created with DB {db_name}", "success")
        return redirect(url_for("auth.list_users"))
    return render_template("register.html", form=form)

# ADMIN PANEL: list, promote/demote, reset password, delete
@auth_bp.route("/users")
@login_required
@admin_required
def list_users():
    users = auth_session.query(AuthUser).order_by(AuthUser.id.desc()).all()
    return render_template("admin_users.html", users=users)

@auth_bp.route("/users/<int:user_id>/make_admin")
@login_required
@admin_required
def make_admin(user_id):
    user = auth_session.query(AuthUser).get(user_id)
    user.role = "admin"
    auth_session.commit()
    flash(f"{user.username} promoted to admin.", "success")
    return redirect(url_for("auth.list_users"))

@auth_bp.route("/users/<int:user_id>/make_user")
@login_required
@admin_required
def make_user(user_id):
    user = auth_session.query(AuthUser).get(user_id)
    user.role = "user"
    auth_session.commit()
    flash(f"{user.username} demoted to user.", "success")
    return redirect(url_for("auth.list_users"))

@auth_bp.route("/users/<int:user_id>/delete")
@login_required
@admin_required
def delete_user(user_id):
    user = auth_session.query(AuthUser).get(user_id)
    auth_session.delete(user)
    auth_session.commit()
    flash(f"{user.username} deleted.", "info")
    return redirect(url_for("auth.list_users"))

@auth_bp.route("/users/<int:user_id>/reset_password", methods=["GET","POST"])
@login_required
@admin_required
def reset_password(user_id):
    user = auth_session.query(AuthUser).get(user_id)
    if request.method=="POST":
        pwd = request.form.get("new_password")
        confirm = request.form.get("confirm_password")
        if not pwd or not confirm:
            flash("Password required", "error")
        elif pwd != confirm:
            flash("Passwords do not match", "error")
        else:
            user.set_password(pwd)
            auth_session.commit()
            flash(f"Password reset for {user.username}", "success")
            return redirect(url_for("auth.list_users"))
    return render_template("admin_reset_password.html", user=user)
