import os
import json
import random
from dotenv import load_dotenv
load_dotenv()  # Load variables from .env

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    college_year = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    questionnaire = db.Column(db.Text, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Registration route – display and process the registration form
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/register', methods=['POST'])
    def register():
        name = request.form.get('name')
        age = request.form.get('age')
        college_year = request.form.get('college_year')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the email is already registered
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in.")
            return redirect(url_for('login'))

        # Create new user and hash the password
        new_user = User(name=name, age=int(age), college_year=college_year, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please log in.")
        return redirect(url_for('login'))

    # Login route – display the login form and process credentials
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            if not user or not user.check_password(password):
                flash("Invalid login credentials. Please try again.")
                return redirect(url_for('login'))
            session['user_id'] = user.id
            flash("Logged in successfully!")
            return redirect(url_for('dashboard'))
        return render_template('login.html')

    # Dashboard – a protected page for logged-in users
    @app.route('/dashboard')
    def dashboard():
        if 'user_id' not in session:
            flash("Please log in to access the dashboard.")
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        return render_template('dashboard.html', user=user)

    # Logout – clear the session
    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash("Logged out successfully!")
        return redirect(url_for('login'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
