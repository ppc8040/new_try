from flask_mail import Mail

mail = Mail()  # Create an instance of Mail

def configure_mail(app):
    """Configures Flask-Mail settings for the app."""
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Change this to your SMTP server
    app.config['MAIL_PORT'] = 465  # Use 587 for TLS
    app.config['MAIL_USE_TLS'] = False  # Set to True if using TLS
    app.config['MAIL_USE_SSL'] = True  # Set to True for SSL
    app.config['MAIL_USERNAME'] = 'indusairuae@gmail.com'
    app.config['MAIL_PASSWORD'] = 'rqeqkkpntikkuqil'
    app.config['MAIL_DEFAULT_SENDER'] = 'indusairuae@gmail.com'

    mail.init_app(app)  # Initialize Flask-Mail with app
    
