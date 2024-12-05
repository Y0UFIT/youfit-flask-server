from app import db

class Fitness(db.Model):
    __tablename__ = 'fitness'

    fitness_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(100), nullable=False)
    run_20 = db.Column(db.String(100))
    treadmil_step = db.Column(db.String(100))
    grip_strength = db.Column(db.String(100), nullable=False)
    sit_up = db.Column(db.String(100), nullable=False)
    bend_forward = db.Column(db.String(100), nullable=False)
    run_10 = db.Column(db.String(100))
    reaction = db.Column(db.String(100))
    long_jump = db.Column(db.String(100))
    flight_time = db.Column(db.String(100))

    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)

    # Relationships
    fitness_results = db.relationship('FitnessResult', backref='fitness', lazy=True)
