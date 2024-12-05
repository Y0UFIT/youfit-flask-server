from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import numpy as np
from scipy.stats import percentileofscore
import pandas as pd
from app import db
from app.models.fitness import Fitness
from app.models.fitness_result import FitnessResult

# Blueprint 설정
fitness_bp = Blueprint('fitness', __name__, url_prefix='/fitness')

# 데이터 파일 경로 (수정 필요)
DATA_PATH = "/Users/jangdabin/Documents/dev/youfit/youfit-flask-server/dataset/measure.csv"

# CSV 데이터 로드
measure = pd.read_csv(DATA_PATH)

# 백분위수 계산 함수
def safe_percentileofscore(data, value):
    valid_data = [x for x in data if x is not None and not np.isnan(x)]
    if len(valid_data) == 0:
        return None
    return percentileofscore(valid_data, value, kind='rank')

@fitness_bp.route('/<int:userId>', methods=['POST'])
def analyze_fitness(userId):
    """
    사용자 체력 데이터를 분석하고 결과를 DB에 저장합니다.
    """
    try:
        input_data = request.get_json()

        # 1. 사용자의 입력값을 fitness 테이블에 저장
        fitness_entry = Fitness(
            user_id=userId,
            date=input_data.get('date'),
            run_20=input_data.get('20_run'),
            treadmil_step=input_data.get('treadmil_step'),
            grip_strength=input_data.get('grip_strength'),
            sit_up=input_data.get('sit_up'),
            bend_forward=input_data.get('bend_forward'),
            run_10=input_data.get('10_run'),
            reaction=input_data.get('reaction'),
            long_jump=input_data.get('long_jump'),
            flight_time=input_data.get('flight_time')
        )
        db.session.add(fitness_entry)
        db.session.flush()  # fitness_id를 바로 가져오기 위해 flush 호출
        print("ok")

        # fitness_id 가져오기
        fitness_id = fitness_entry.fitness_id

        # 2. 입력 데이터 분석
        # 그룹화 항목 처리
        group_pairs = {
            "20_run_treadmil": ("20_run", "treadmil_step"),
            "10_run_reaction": ("10_run", "reaction"),
            "long_jump_flight": ("long_jump", "flight_time")
        }

        # 분석 결과 저장
        percentile_scores = []

        # 그룹 항목 분석
        for group, (col1, col2) in group_pairs.items():
            chosen_col = col1 if input_data.get(col1) is not None else col2
            value = input_data.get(chosen_col, None)
            if value is not None:
                percentile = safe_percentileofscore(measure[chosen_col], value)
                if percentile is not None:
                    top_percent = 100 - percentile
                    percentile_scores.append(top_percent)

        # 개별 항목 분석
        for col in ["grip_strength", "sit_up", "bend_forward"]:
            value = input_data.get(col, None)
            if value is not None:
                percentile = safe_percentileofscore(measure[col], value)
                if percentile is not None:
                    top_percent = 100 - percentile
                    percentile_scores.append(top_percent)

        # 평균 백분위 계산
        percent = int(np.mean(percentile_scores)) if percentile_scores else None

        # 3. DB에 FitnessResult 저장
        fitness_result = FitnessResult(
            percent=percent,
            cardio=input_data.get('cardio', "Unknown"),  # 기본값 설정
            muscular_strength=input_data.get('muscular_strength', "Unknown"),
            muscular_endurance=input_data.get('muscular_endurance', "Unknown"),
            flexibility=input_data.get('flexibility', "Unknown"),
            agility=input_data.get('agility', "Unknown"),
            power=input_data.get('power', "Unknown"),
            change_chart=input_data.get('change_chart', "default_value"),
            fitness_id=fitness_id
        )
        db.session.add(fitness_result)
        db.session.commit()

        # 결과 반환
        return jsonify({
            "fitnessId": fitness_id,
            "percent": fitness_result.percent
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
