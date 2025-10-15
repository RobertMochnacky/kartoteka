from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
# app/main.py
from .models import Customer


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
    # Fetch all customers with their activity reports
    customers = Customer.query.all()
    return render_template("dashboard.html", user=current_user, customers=customers)

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
