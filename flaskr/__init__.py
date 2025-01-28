import os
from flask import Flask, request, session, redirect, render_template, url_for
from flask_login import LoginManager, login_user, logout_user
from flaskr.models import db, User, Inventory
from flaskr.final_db import run_data_update
import time
import threading
from flaskr.home import home_bp
from flaskr.views import views
import pytz

def create_app():
    app = Flask(__name__)
    app.secret_key = "qwerty123456"

    # Initialize LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'render_login'

    # Setup config for database
    uri = os.environ.get("HEROKU_POSTGRESQL_GREEN_URL") 
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # User loader function for login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Route for rendering login page
    @app.route('/login', methods=['GET'])
    def render_login():
        return render_template('index.html')

    # Route for handling login
    @app.route('/login_user', methods=['POST'])
    def login():
        """Login logic."""
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            session['username'] = username
            return redirect(url_for('views.home'))
        else:
            return render_template('index.html', error='Invalid username or password.')

    # Route for logout
    @app.route('/logout')
    def logout():
        logout_user()
        session.pop('username', None)
        return redirect(url_for('homepage.home'))

    # Register blueprints and create tables
    with app.app_context():
        db.create_all()
        app.register_blueprint(home_bp)
        app.register_blueprint(views, url_prefix='/views')

    def schedule_updates():
    # Define the GST time zone
    gst_timezone = pytz.timezone("Asia/Dubai")

    # Custom job function to run data update at specific times
    def run_data_update_with_timezone():
        # Get the current time in GST
        now = datetime.now(gst_timezone)
        print(f"Running update at GST time: {now.strftime('%Y-%m-%d %H:%M:%S')}")  
        run_data_update()

    # Job runner function to check current time and trigger updates
    def job_runner():
        while True:
            #Get current GST time
            current_time_gst = datetime.now(gst_timezone).strftime("%H:%M")
            if current_time_gst == "07:00" or current_time_gst == "16:00":
                run_data_update_with_timezone()
                time.sleep(60)  # Wait for a minute to avoid running multiple times in the same minute
            time.sleep(1)  # Check every second

    # Start the job runner in a daemon thread
    threading.Thread(target=job_runner, daemon=True).start()

    # Start the scheduler
    schedule_updates()

    return app
