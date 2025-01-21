import os
from flask import Flask, request, session, redirect, render_template, url_for
from flask_login import LoginManager, login_user, logout_user
from flaskr.models import db, User, Inventory

from flaskr.home import home_bp
from flaskr.views import views

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

    return app
