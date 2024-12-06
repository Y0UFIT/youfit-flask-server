from app import db

class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    dateOfBirth = db.Column(db.String(100), nullable=True)
    full_name = db.Column(db.String(100), nullable=True)
    gender = db.Column(db.String(50), nullable=True)

    # Relationships 
    fitness = db.relationship('Fitness', backref='user', lazy=True)