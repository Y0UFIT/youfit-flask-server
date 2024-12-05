from flask import Blueprint, request, jsonify
from app import db
from app.models.exercise import Exercise
from app.models.fitness import Fitness
from app.models.fitness_result import FitnessResult
from collections import defaultdict

# Blueprint 생성
exercise_bp = Blueprint('exercise', __name__)

# 운동 데이터를 추천하는 라우트 (user_id 기반)
@exercise_bp.route('/exercise/recommend/<int:user_id>', methods=['GET'])
def get_exercises(user_id):
    try:
        # user_id를 기반으로 fitness 데이터를 가져오기
        fitness_data = Fitness.query.filter(Fitness.user_id == user_id).all()

        # 유저의 fitness 데이터가 없을 경우
        if not fitness_data:
            return jsonify({"message": "No fitness data found for this user"}), 404

        # 운동 데이터를 날짜별로 그룹화
        exercises = defaultdict(list)

        # fitness_data에 해당하는 fitness_result_id를 통해 Exercise 데이터를 가져오기
        for fitness in fitness_data:
            # fitness_id를 기준으로 fitness_result를 가져오기
            fitness_results = FitnessResult.query.filter(FitnessResult.fitness_id == fitness.fitness_id).all()

            for fitness_result in fitness_results:
                # fitness_result_id를 기준으로 Exercise 데이터를 가져오기
                exercise_results = Exercise.query.filter(Exercise.fitness_result_id == fitness_result.fitness_result_id).all()

                for exercise in exercise_results:
                    # 날짜를 기준으로 운동을 그룹화
                    exercises[fitness.date].append({
                        "exercise_name": exercise.exercise_name,
                        "exercise_url": exercise.exercise_url
                    })

        # 날짜별로 정렬 및 포맷 맞추기
        exercise_list = []
        for date, exercise_group in exercises.items():
            exercise_list.append({
                "date": date,
                "exercise": [
                    {"exerciseName": exercise["exercise_name"], "exerciseUrl": exercise["exercise_url"]}
                    for exercise in exercise_group
                ]
            })

        # 운동 데이터를 찾지 못한 경우
        if not exercise_list:
            return jsonify({"message": "No exercises found for this user's fitness data"}), 404

        # 성공적으로 운동 데이터 반환
        return jsonify({"exercises": exercise_list})

    except Exception as e:
        # 예외 처리
        return jsonify({"message": str(e)}), 500
