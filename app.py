import os
import json
import random
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

# Initialize extensions
db = SQLAlchemy()
mail = Mail()

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    college_year = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    otp = db.Column(db.String(6), nullable=True)
    verified = db.Column(db.Boolean, default=False)
    questionnaire = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<User {self.name}>'

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')

    # Database configuration (SQLite used here)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Mail configuration for Gmail with App Password
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False') == 'True'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your_app_password')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'your_email@gmail.com')
    app.config['TESTING'] = False
    app.config['MAIL_SUPPRESS_SEND'] = False
    app.config['MAIL_DEBUG'] = True

    # Initialize extensions with the app instance
    db.init_app(app)
    mail.init_app(app)

    # Create all database tables within an app context
    with app.app_context():
        db.create_all()

    ####################################
    # Routes for Registration and OTP  #
    ####################################
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/register', methods=['POST'])
    def register():
        name = request.form.get('name')
        age = request.form.get('age')
        college_year = request.form.get('college_year')
        email = request.form.get('email')

        # Check for duplicate registration by email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in.")
            return redirect(url_for('login'))

        # Generate a 6-digit OTP
        otp = str(random.randint(100000, 999999))
        new_user = User(
            name=name,
            age=int(age),
            college_year=college_year,
            email=email,
            otp=otp,
            verified=False
        )
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Database error occurred. Please try again.")
            return redirect(url_for('index'))

        # Send OTP email for registration
        try:
            msg = Message("Your Verification OTP",
                          sender=app.config['MAIL_DEFAULT_SENDER'],
                          recipients=[email])
            msg.body = f"Hello {name},\n\nYour OTP code is: {otp}\n\nThank you."
            mail.send(msg)
        except Exception as e:
            print("Mail Sending Error:", e)
            flash("Error sending verification email. Check your SMTP settings.")

        # Render the verification page; pass mode to distinguish registration from login
        return render_template('verify.html', user_id=new_user.id, mode="register")

    ##########################
    # OTP-based Verification #
    ##########################
    @app.route('/verify', methods=['POST'])
    def verify():
        user_id = request.form.get('user_id')
        user_input_otp = request.form.get('otp')
        mode = request.form.get('mode')  # "register" or "login"
        user = User.query.get(user_id)
        if user and user.otp == user_input_otp:
            user.verified = True
            db.session.commit()
            if mode == "login":
                # Set session for logged-in user
                session['user_id'] = user.id
                flash("Logged in successfully!")
                return redirect(url_for('dashboard'))
            else:
                # For new registration, move to the questionnaire
                return render_template('questionnaire.html', user_id=user_id)
        else:
            flash("Invalid OTP. Please try again.")
            if mode == "login":
                return redirect(url_for('login'))
            else:
                return redirect(url_for('index'))

    @app.route('/submit_questionnaire', methods=['POST'])
    def submit_questionnaire():
        user_id = request.form.get('user_id')
        responses = { key: value for key, value in request.form.items() if key != 'user_id' }
        user = User.query.get(user_id)
        if user and user.verified:
            user.questionnaire = json.dumps(responses)
            db.session.commit()
            flash("Questionnaire submitted successfully!")
            # Optionally, log in the user after registration:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash("User verification failed.")
            return redirect(url_for('index'))

    ######################
    # OTP-Based Login    #
    ######################
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            user = User.query.filter_by(email=email).first()
            if not user:
                flash("Email not registered. Please register first.")
                return redirect(url_for('index'))
            # Generate a new OTP for login and update the user record
            user.otp = str(random.randint(100000, 999999))
            db.session.commit()
            try:
                msg = Message("Your Login OTP",
                              sender=app.config['MAIL_DEFAULT_SENDER'],
                              recipients=[email])
                msg.body = f"Hello {user.name},\n\nYour login OTP code is: {user.otp}\n\nThank you."
                mail.send(msg)
            except Exception as e:
                print("Mail Sending Error:", e)
                flash("Error sending OTP. Please try again later.")
                return redirect(url_for('login'))
            return render_template('verify.html', user_id=user.id, mode="login")
        return render_template('login.html')

    ##################
    # Dashboard      #
    ##################
    @app.route('/dashboard')
    def dashboard():
        if 'user_id' not in session:
            flash("Please log in to access the dashboard.")
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        return render_template('dashboard.html', user=user)

    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash("Logged out successfully!")
        return redirect(url_for('login'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
