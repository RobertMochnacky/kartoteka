from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .models import User, Customer

main_bp = Blueprint("main", __name__)

@main_bp.route("/dashboard")
@login_required
def dashboard():
    # Fetch all customers with their activity reports
    customers = Customer.query.all()
    return render_template("dashboard.html", user=current_user, customers=customers)
