from flask import render_template, Blueprint, session, redirect, url_for
from flask_login import login_required

home_bp = Blueprint('homepage', __name__)


@home_bp.route('/')
@login_required
def home():
    """Redirect to the views home page after login."""
    if 'username' in session:
        return redirect(url_for('views.home'))  # Redirecting to views.py's home
    return render_template('index.html')
