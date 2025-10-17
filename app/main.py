from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, Response
from flask_login import login_required, current_user
from .models import Customer, Activity, User
from . import db
from sqlalchemy import or_, and_
from datetime import datetime
import io
import csv
import pandas as pd
from werkzeug.utils import secure_filename
import os
from flask_babel import _
import uuid

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
            flash(_("Activity text is required."), "danger")
            return redirect(url_for("main.add_activity", customer_id=customer.id))

        activity = Activity(
            text=text,
            customer_id=customer.id,
            creator_id=current_user.id
        )
        db.session.add(activity)
        db.session.commit()
        flash(_("Activity added successfully."), "success")
        return redirect(url_for("main.view_customer", customer_id=customer.id))

    return render_template("add_activity.html", customer=customer)

@main_bp.route("/add_activity", methods=["POST"])
@login_required
def add_activity_from_activities():
    customer_id = request.form.get("customer_id")
    text = request.form.get("activity_text")

    if not customer_id or not text:
        flash(_("Customer and Activity text are required."), "danger")
        return redirect(url_for("main.activities"))

    activity = Activity(
        text=text,
        customer_id=int(customer_id),
        creator_id=current_user.id
    )
    db.session.add(activity)
    db.session.commit()
    flash(_("Activity added successfully."), "success")
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
            flash(_("Activity text is required."), "danger")
            return redirect(url_for("main.edit_activity", activity_id=activity.id))

        activity.text = text
        if customer_id:
            activity.customer_id = int(customer_id)
        db.session.commit()
        flash(_("Activity updated successfully."), "success")
        return redirect(url_for("main.activities"))

    return render_template("edit_activity.html", activity=activity, customers=customers)

@main_bp.route("/edit_activity_ajax/<int:activity_id>", methods=["POST"])
@login_required
def edit_activity_ajax(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    text = request.form.get("text")
    customer_id = request.form.get("customer_id")

    if not text:
        return jsonify({"success": False, "message": _("Activity text is required.")})

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
    flash(_("Activity deleted successfully."), "success")
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
    search_query = request.args.get("q", "", type=str)

    query = Customer.query
    if search_query:
        query = query.filter(
            or_(
                Customer.name.ilike(f"%{search_query}%"),
                Customer.email.ilike(f"%{search_query}%"),
                Customer.phone.ilike(f"%{search_query}%")
            )
        )

    customers = query.order_by(Customer.name).all()
    return render_template("customers.html", customers=customers, search_query=search_query)

@main_bp.route("/customer/<int:customer_id>")
@login_required
def view_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    # Fetch activities sorted by timestamp descending
    activities = (
        Activity.query
        .filter_by(customer_id=customer.id)
        .order_by(Activity.timestamp.desc())
        .all()
    )
    return render_template("view_customer.html", customer=customer, activities=activities)

@main_bp.route("/add_customer", methods=["GET", "POST"])
@login_required
def add_customer():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form.get("phone")
        address = request.form.get("address")

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
        flash(_("Customer added successfully!"))
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
        flash(_("Customer updated!"))
        return redirect(url_for("main.view_customer", customer_id=customer.id))

    return render_template("edit_customer.html", customer=customer)

@main_bp.route("/delete_customer/<int:customer_id>")
@login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash(_("Customer deleted!"))
    return redirect(url_for("main.customers"))

@main_bp.route("/search_customers")
@login_required
def search_customers():
    query = request.args.get("q", "").strip()
    if query:
        customers = Customer.query.filter(
            or_(
                Customer.name.ilike(f"%{query}%"),
                Customer.email.ilike(f"%{query}%"),
                Customer.phone.ilike(f"%{query}%"),
                Customer.address.ilike(f"%{query}%")
            )
        ).all()
    else:
        customers = Customer.query.all()

    # Return JSON data
    results = []
    for c in customers:
        results.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "address": c.address
        })
    return jsonify(results)

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

# ----------------------------
# Export Customers
# ----------------------------
@main_bp.route("/export/customers")
@login_required
def export_customers():
    customers = Customer.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Email", "Phone", "Address"])
    for c in customers:
        writer.writerow([c.id, c.name, c.email, c.phone, c.address])
    
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=customers.csv"}
    )

# ----------------------------
# Export Activities
# ----------------------------
@main_bp.route("/export/activities")
@login_required
def export_activities():
    activities = Activity.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "CustomerID", "CustomerName", "Text", "Creator", "Timestamp"])
    for a in activities:
        writer.writerow([a.id, a.customer.id, a.customer.name, a.text, a.creator.username, a.timestamp])
    
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=activities.csv"}
    )

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route("/import/customers", methods=["GET", "POST"])
@login_required
def import_customers():    
    if request.method == "POST":
        if "file" not in request.files:
            flash(_("No file part"), "warning")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash(_("No selected file"), "warning")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            df = pd.read_csv(file, dtype=str)  # force all columns as strings
            df = df.fillna("")  # replace NaN with empty strings

            added_count = 0
            skipped_count = 0

            for _, row in df.iterrows():
                name = row.get("Name", "").strip() or _("Unnamed Customer")
                email = row.get("Email", "").strip()
                phone = row.get("Phone", "").strip()
                address = row.get("Address", "").strip()

                # ✅ If all are empty, generate unique placeholder values
                if not email:
                    email = f"placeholder_{uuid.uuid4().hex[:8]}@example.com"
                if not phone:
                    phone = f"000-{uuid.uuid4().hex[:4]}"
                if not address:
                    address = f"Unknown Address {uuid.uuid4().hex[:4]}"

                # ✅ Check for existing by email only if valid (not placeholder)
                existing = Customer.query.filter_by(email=email).first()
                if existing:
                    skipped_count += 1
                    continue

                customer = Customer(
                    name=name,
                    email=email,
                    phone=phone,
                    address=address
                )
                db.session.add(customer)
                added_count += 1

            db.session.commit()

            flash(
                _("Customers imported successfully — %(added)d added, %(skipped)d skipped.", 
                  added=added_count, skipped=skipped_count),
                "success"
            )

            return redirect(url_for("main.customers"))

    return render_template("import_customers.html")

@main_bp.route("/import/activities", methods=["GET", "POST"])
@login_required
def import_activities():
    if request.method == "POST":
        file = request.files.get("file")
        if file and allowed_file(file.filename):
            df = pd.read_csv(file)
            for _, row in df.iterrows():
                customer = Customer.query.get(row["CustomerID"])
                creator = User.query.filter_by(username=row["Creator"]).first()  # adjust as needed
                if customer and creator:
                    activity = Activity(
                        customer_id=customer.id,
                        text=row["Text"],
                        creator_id=creator.id,
                        timestamp=pd.to_datetime(row["Timestamp"])
                    )
                    db.session.add(activity)
            db.session.commit()
            flash(_("Activities imported successfully"))
            return redirect(url_for("main.activities"))
    return render_template("import_activities.html")

