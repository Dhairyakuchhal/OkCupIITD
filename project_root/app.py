import os
import json
import random
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with an actual secret

# Configure the database URI. To switch to PostgreSQL later, change this URI accordingly.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail Configuration (Adjust to your email server)
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@example.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'

db = SQLAlchemy(app)
mail = Mail(app)

# Import your models after initializing db
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

# Create the database tables if they don't exist.
@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    age = request.form.get('age')
    college_year = request.form.get('college_year')
    email = request.form.get('email')

    # Generate a 6-digit OTP code.
    otp = str(random.randint(100000, 999999))
    
    # Create a new user record
    new_user = User(name=name, age=int(age), college_year=college_year, email=email, otp=otp, verified=False)
    db.session.add(new_user)
    db.session.commit()

    try:
        msg = Message("Your Verification OTP", sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f"Hello {name},\n\nYour OTP code is: {otp}\n\nThank you."
        mail.send(msg)
    except Exception as e:
        print("Mail Sending Error:", e)
    
    # Pass the user ID to the verification page.
    return render_template('verify.html', user_id=new_user.id)

@app.route('/verify', methods=['POST'])
def verify():
    user_id = request.form.get('user_id')
    user_input_otp = request.form.get('otp')
    user = User.query.get(user_id)
    
    if user and user.otp == user_input_otp:
        user.verified = True
        db.session.commit()
        return render_template('questionnaire.html', user_id=user_id)
    else:
        flash('Invalid OTP. Please try again.')
        return redirect(url_for('index'))

@app.route('/submit_questionnaire', methods=['POST'])
def submit_questionnaire():
    user_id = request.form.get('user_id')
    # Exclude the hidden 'user_id' field and store remaining responses as JSON.
    responses = { key: value for key, value in request.form.items() if key != 'user_id' }
    user = User.query.get(user_id)
    
    if user and user.verified:
        user.questionnaire = json.dumps(responses)
        db.session.commit()
        return "Questionnaire submitted successfully. You can now be matched!"
    else:
        flash('User verification failed.')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
