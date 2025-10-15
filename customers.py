from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Customer, ActivityReport
from forms import CustomerForm, ActivityReportForm

customers_bp = Blueprint("customers", __name__)

# Create a new customer
@customers_bp.route("/customers/new", methods=["GET", "POST"])
@login_required
def new_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(name=form.name.data, email=form.email.data)
        db.session.add(customer)
        db.session.commit()
        flash("Customer added successfully.", "success")
        return redirect(url_for("customers.list_customers"))
    return render_template("new_customer.html", form=form)

# List all customers
@customers_bp.route("/customers")
@login_required
def list_customers():
    customers = Customer.query.all()
    return render_template("customers.html", customers=customers)

# Add activity report for a customer
@customers_bp.route("/customers/<int:customer_id>/activities/new", methods=["GET", "POST"])
@login_required
def new_activity(customer_id):
    form = ActivityReportForm()
    customer = Customer.query.get_or_404(customer_id)
    if form.validate_on_submit():
        activity = ActivityReport(
            customer_id=customer.id,
            creator_id=current_user.id,
            description=form.description.data
        )
        db.session.add(activity)
        db.session.commit()
        flash("Activity added successfully.", "success")
        return redirect(url_for("customers.list_customers"))
    return render_template("new_activity.html", form=form, customer=customer)

# List activities for a customer
@customers_bp.route("/customers/<int:customer_id>/activities")
@login_required
def list_activities(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    activities = ActivityReport.query.filter_by(customer_id=customer.id).all()
    return render_template("activities.html", customer=customer, activities=activities)
