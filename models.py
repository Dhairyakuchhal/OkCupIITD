from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    college_year = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    otp = db.Column(db.String(6), nullable=True)
    verified = db.Column(db.Boolean, default=False)
    # Save questionnaire responses as a JSON string
    questionnaire = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<User {self.name}>'
