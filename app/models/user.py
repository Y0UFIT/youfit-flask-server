from app import db

class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)

    # Relationships
    fitness = db.relationship('Fitness', backref='user', lazy=True)