from ..extensions import db

class FitnessResult(db.Model):
    __tablename__ = 'fitness_result'

    fitness_result_id = db.Column(db.Integer, primary_key=True)
    percent = db.Column(db.Integer, nullable=False)
    cardio = db.Column(db.String(100), nullable=False)
    muscular_strength = db.Column(db.String(100), nullable=False)
    muscular_endurance = db.Column(db.String(100), nullable=False)
    flexibility = db.Column(db.String(100), nullable=False)
    agility = db.Column(db.String(100), nullable=False)
    power = db.Column(db.String(100), nullable=False)

    fitness_id = db.Column(db.Integer, db.ForeignKey('fitness.fitness_id'), nullable=False)

    # Relationships
    exercises = db.relationship('Exercise', backref='fitness_result', lazy=True)
