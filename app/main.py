from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
# app/main.py
from .models import Customer, Activity
from . import db
from sqlalchemy import or_, and_
from datetime import datetime

main_bp = Blueprint("main", __name__)

#@main_bp.route("/dashboard")
#def dashboard():
#    return "<h1>Dashboard works!</h1>"

@main_bp.route("/")
def index():
    # Redirect to dashboard
    return redirect(url_for("main.dashboard"))

@main_bp.route("/dashboard")
@login_required
def dashboard():
    customers = Customer.query.all()
    # Show recent 5 activities
    activities = Activity.query.join(Customer).join(User)\
        .order_by(Activity.timestamp.desc())\
        .limit(5).all()
    return render_template("dashboard.html", customers=customers, activities=activities)

@main_bp.route("/add_customer", methods=["GET", "POST"])
@login_required
def add_customer():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]

        if not name or not email:
            flash("Name and Email are required!")
            return redirect(url_for("main.add_customer"))
            
        customer = Customer(name=name, email=email)
        db.session.add(customer)
        db.session.commit()
        flash("Customer added successfully!")
        return redirect(url_for("main.dashboard"))
        
    return render_template("add_customer.html")

@main_bp.route("/edit_customer/<int:customer_id>", methods=["GET", "POST"])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == "POST":
        customer.name = request.form["name"]
        customer.email = request.form["email"]
        db.session.commit()
        flash("Customer updated!")
        return redirect(url_for("main.dashboard"))

    return render_template("edit_customer.html", customer=customer)

@main_bp.route("/delete_customer/<int:customer_id>")
@login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash("Customer deleted!")
    return redirect(url_for("main.dashboard"))

@main_bp.route("/add_activity/<int:customer_id>", methods=["GET", "POST"])
@login_required
def add_activity(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == "POST":
        text = request.form.get("text")

        if not text:
            flash("Activity text is required.", "danger")
            return redirect(url_for("main.add_activity", customer_id=customer.id))

        # Create the activity and assign current user as creator
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

@main_bp.route("/customer/<int:customer_id>")
@login_required
def view_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template("view_customer.html", customer=customer)

@main_bp.route("/activities")
@login_required
def activities():
    # Get filter parameters from query string
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
    customers = Customer.query.all()  # For filter dropdown
    return render_template("activities.html", activities=activities, customers=customers,
                           filter_customer_id=customer_id, filter_text=text,
                           filter_start_date=start_date, filter_end_date=end_date)

@main_bp.route("/customers")
@login_required
def customers():
    customers = Customer.query.all()
    return render_template("customers.html", customers=customers)
