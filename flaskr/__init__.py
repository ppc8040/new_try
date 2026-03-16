import os
import time
import threading
from flask import Flask, request, session, redirect, render_template, url_for
from flask_login import LoginManager, login_user, logout_user
from flaskr.models import db, User, Inventory
from flaskr.final_db import run_data_update, sync_users_from_excel
from flaskr.home import home_bp
from flaskr.views import views


def create_app():
    app = Flask(__name__)
    app.secret_key = "qwerty123456"

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'render_login'

    uri = os.environ.get("HEROKU_POSTGRESQL_GREEN_URL")
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.route('/login', methods=['GET'])
    def render_login():
        return render_template('index.html')

    @app.route('/login_user', methods=['POST'])
    def login():
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            session['username'] = username
            return redirect(url_for('views.home'))
        else:
            return render_template('index.html', error='Invalid username or password.')

        @app.route('/add-customer-code-col')
        def add_customer_code_col():
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS customer_code VARCHAR(20);'))
                    conn.commit()
                return "Done - customer_code column added to user table."
            except Exception as e:
                return f"Error: {str(e)}"

    @app.route('/logout')
    def logout():
        logout_user()
        session.pop('username', None)
        return redirect(url_for('homepage.home'))

    app.register_blueprint(home_bp)
    app.register_blueprint(views, url_prefix='/views')

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"db.create_all() warning (non-fatal): {e}")

    def schedule_updates():
        import schedule
        schedule.every(1).hours.do(run_data_update)
        schedule.every(1).hours.do(sync_users_from_excel)

        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(1)

        threading.Thread(target=run_scheduler, daemon=True).start()

    schedule_updates()

    return app
