import os
import time
import threading
import logging
from flask import Flask, request, session, redirect, render_template, url_for
from flask_login import LoginManager, login_user, logout_user
from flaskr.models import db, User, Inventory, LoginEvent
from flaskr.final_db import run_data_update
from flaskr.home import home_bp
from flaskr.views import views

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            # Track successful login: record username + real client IP
            try:
                forwarded_for = request.headers.get('X-Forwarded-For', request.remote_addr)
                client_ip = forwarded_for.split(',')[0].strip()
                event = LoginEvent(username=username, ip_address=client_ip)
                db.session.add(event)
                db.session.commit()
            except Exception:
                # Non-fatal: login still succeeds even if tracking fails
                db.session.rollback()
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

    # ── SCHEDULER ──────────────────────────────────────────────────────────────
    _scheduler_started = threading.Event()

    def run_scheduler():
        import schedule

        # Run once immediately on startup so data is fresh after any dyno restart
        logger.info("[Scheduler] Running initial data update on startup...")
        try:
            run_data_update()
            logger.info("[Scheduler] Initial data update complete.")
        except Exception as e:
            logger.error(f"[Scheduler] Initial data update failed: {e}")

        schedule.every(1).hours.do(_scheduled_job)
        _scheduler_started.set()
        logger.info("[Scheduler] Hourly refresh scheduled. Entering loop.")

        while True:
            schedule.run_pending()
            time.sleep(30)  # check every 30s instead of every 1s — less CPU waste

    def _scheduled_job():
        logger.info("[Scheduler] Hourly trigger fired — running data update...")
        try:
            run_data_update()
            logger.info("[Scheduler] Hourly data update complete.")
        except Exception as e:
            logger.error(f"[Scheduler] Hourly data update failed: {e}")

    def watchdog():
        """Restarts the scheduler thread if it ever dies."""
        _scheduler_started.wait()  # wait until first scheduler thread is actually running
        while True:
            time.sleep(60)
            if not scheduler_thread.is_alive():
                logger.warning("[Watchdog] Scheduler thread died — restarting...")
                new_thread = threading.Thread(target=run_scheduler, daemon=True, name="scheduler")
                new_thread.start()

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True, name="scheduler")
    scheduler_thread.start()
    threading.Thread(target=watchdog, daemon=True, name="watchdog").start()
    # ── END SCHEDULER ──────────────────────────────────────────────────────────

    return app
