from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from .models import Customer, Activity, User
from . import db
from sqlalchemy import or_, and_
from datetime import datetime

main_bp = Blueprint("main", __name__)

# -----------------------------
# Context processor for user colors
# -----------------------------
@main_bp.context_processor
def inject_user_colors():
    if current_user.is_authenticated:
        return {
            "primary_color": current_user.primary_color or "#3a86ff",
            "sidebar_bg_color": current_user.sidebar_bg_color or "#fff",
            "text_color": current_user.text_color or "#212529"
        }
    return {}

# -----------------------------
# Index / Dashboard
# -----------------------------
@main_bp.route("/")
def index():
    return redirect(url_for("main.dashboard"))

@main_bp.route("/dashboard")
@login_required
def dashboard():
    customers = Customer.query.all()

    try:
        limit = int(request.args.get("recent_limit", 5))
    except ValueError:
        limit = 5

    if limit not in [5, 10, 15, 20, 30]:
        limit = 5

    activities = (
        Activity.query.join(Customer)
        .join(User)
        .order_by(Activity.timestamp.desc())
        .limit(limit)
        .all()
    )

    return render_template(
        "dashboard.html",
        customers=customers,
        activities=activities,
        recent_limit=limit
    )

# -----------------------------
# Activities routes
# -----------------------------
@main_bp.route("/add_activity/<int:customer_id>", methods=["GET", "POST"])
@login_required
def add_activity(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == "POST":
        text = request.form.get("text")
        if not text:
            flash("Activity text is required.", "danger")
            return redirect(url_for("main.add_activity", customer_id=customer.id))

        activity = Activity(
            text=text,
            customer_id=customer.id,
            creator_id=current_user.id
        )
        db.session.add(activity)
        db.session.commit()
        flash("Activity added successfully.", "success")
        return redirect(url_for("main.view_customer", customer_id=customer.id))

    return render_template("add_activity.html", customer=customer)

@main_bp.route("/add_activity", methods=["POST"])
@login_required
def add_activity_from_activities():
    customer_id = request.form.get("customer_id")
    text = request.form.get("activity_text")

    if not customer_id or not text:
        flash("Customer and Activity text are required.", "danger")
        return redirect(url_for("main.activities"))

    activity = Activity(
        text=text,
        customer_id=int(customer_id),
        creator_id=current_user.id
    )
    db.session.add(activity)
    db.session.commit()
    flash("Activity added successfully.", "success")
    return redirect(url_for("main.activities"))

@main_bp.route("/edit_activity/<int:activity_id>", methods=["GET", "POST"])
@login_required
def edit_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    customers = Customer.query.all()

    if request.method == "POST":
        text = request.form.get("text")
        customer_id = request.form.get("customer_id")

        if not text:
            flash("Activity text is required.", "danger")
            return redirect(url_for("main.edit_activity", activity_id=activity.id))

        activity.text = text
        if customer_id:
            activity.customer_id = int(customer_id)
        db.session.commit()
        flash("Activity updated successfully.", "success")
        return redirect(url_for("main.activities"))

    return render_template("edit_activity.html", activity=activity, customers=customers)

@main_bp.route("/edit_activity_ajax/<int:activity_id>", methods=["POST"])
@login_required
def edit_activity_ajax(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    text = request.form.get("text")
    customer_id = request.form.get("customer_id")

    if not text:
        return jsonify({"success": False, "message": "Activity text is required."})

    activity.text = text
    if customer_id:
        activity.customer_id = int(customer_id)
    db.session.commit()

    return jsonify({
        "success": True,
        "text": activity.text,
        "customer_name": activity.customer.name,
        "timestamp": activity.timestamp.strftime('%Y-%m-%d %H:%M')
    })

@main_bp.route("/delete_activity/<int:activity_id>", methods=["POST", "GET"])
@login_required
def delete_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    db.session.delete(activity)
    db.session.commit()
    flash("Activity deleted successfully.", "success")
    return redirect(url_for("main.activities"))

@main_bp.route("/activities")
@login_required
def activities():
    customer_id = request.args.get("customer_id", type=int)
    text = request.args.get("text", type=str)
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = Activity.query.join(Customer).join(User)

    if customer_id:
        query = query.filter(Activity.customer_id == customer_id)
    if text:
        query = query.filter(Activity.text.ilike(f"%{text}%"))
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(Activity.timestamp >= start_dt)
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(Activity.timestamp <= end_dt)

    activities = query.order_by(Activity.timestamp.desc()).all()
    customers = Customer.query.all()
    return render_template(
        "activities.html",
        activities=activities,
        customers=customers,
        filter_customer_id=customer_id,
        filter_text=text,
        filter_start_date=start_date,
        filter_end_date=end_date
    )

# -----------------------------
# Customers routes
# -----------------------------
@main_bp.route("/customers")
@login_required
def customers():
    customers = Customer.query.all()
    return render_template("customers.html", customers=customers)

@main_bp.route("/customer/<int:customer_id>")
@login_required
def view_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template("view_customer.html", customer=customer)

@main_bp.route("/add_customer", methods=["GET", "POST"])
@login_required
def add_customer():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form.get("phone") or "0000 000 000"
        address = request.form.get("address") or "Unknown"

        if not name:
            flash("Name field is required!")
            return redirect(url_for("main.add_customer"))

        customer = Customer(
            name=name,
            email=email,
            phone=phone,
            address=address
        )
        db.session.add(customer)
        db.session.commit()
        flash("Customer added successfully!")
        return redirect(url_for("main.customers"))

    return render_template("add_customer.html")

@main_bp.route("/edit_customer/<int:customer_id>", methods=["GET", "POST"])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == "POST":
        customer.name = request.form.get("name")
        customer.email = request.form.get("email")
        customer.phone = request.form.get("phone") or "0000 000 000"
        customer.address = request.form.get("address") or "Unknown"
        db.session.commit()
        flash("Customer updated!")
        return redirect(url_for("main.view_customer", customer_id=customer.id))

    return render_template("edit_customer.html", customer=customer)

@main_bp.route("/delete_customer/<int:customer_id>")
@login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash("Customer deleted!")
    return redirect(url_for("main.dashboard"))

# -----------------------------
# Settings routes
# -----------------------------
@main_bp.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

@main_bp.route("/save_settings", methods=["POST"])
@login_required
def save_settings():
    data = request.get_json()
    current_user.primary_color = data.get("primary_color", current_user.primary_color)
    current_user.sidebar_bg_color = data.get("sidebar_bg_color", current_user.sidebar_bg_color)
    current_user.text_color = data.get("text_color", current_user.text_color)
    current_user.theme = data.get("theme", current_user.theme)
    db.session.commit()
    return jsonify({"status": "success"})
