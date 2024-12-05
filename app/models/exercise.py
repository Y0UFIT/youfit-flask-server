from app import db

class Exercise(db.Model):
    __tablename__ = 'exercise'

    exercise_id = db.Column(db.Integer, primary_key=True)
    exercise_name = db.Column(db.String(100), nullable=False)
    exercise_url = db.Column(db.String(300), nullable=False)

    fitness_result_id = db.Column(db.Integer, db.ForeignKey('fitness_result.fitness_result_id'), nullable=False)
