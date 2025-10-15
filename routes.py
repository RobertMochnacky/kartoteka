from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Customer, ActivityReport
from app.forms import CustomerForm, ActivityForm

routes_bp = Blueprint("routes", __name__)

@routes_bp.route("/")
@login_required
def index():
    return render_template("index.html", user=current_user)

@app.route('/customers')
@login_required
def customers():
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)

@app.route('/customer/new', methods=['GET', 'POST'])
@login_required
def new_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(name=form.name.data, email=form.email.data)
        db.session.add(customer)
        db.session.commit()
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers'))
    return render_template('new_customer.html', form=form)

@app.route('/customer/<int:customer_id>/activities')
@login_required
def customer_activities(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    activities = ActivityReport.query.filter_by(customer_id=customer.id).all()
    return render_template('activities.html', customer=customer, activities=activities)

@app.route('/activity/new/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def new_activity(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    form = ActivityForm()
    if form.validate_on_submit():
        activity = ActivityReport(content=form.content.data, customer=customer)
        db.session.add(activity)
        db.session.commit()
        flash('Activity added successfully!', 'success')
        return redirect(url_for('customer_activities', customer_id=customer.id))
    return render_template('new_activity.html', form=form, customer=customer)
