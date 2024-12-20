import matplotlib
matplotlib.use('Agg')

from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from data.exercise_data import exercise_data, category_mapping
import numpy as np
from scipy.stats import percentileofscore
import pandas as pd
from app import db
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from collections import defaultdict
from app.models.fitness import Fitness
from app.models.fitness_result import FitnessResult
from app.models.exercise import Exercise
from app.models.user import User

import boto3
import os
import json
import random

# AWS 설정
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name='ap-northeast-2'
)
s3_url=os.environ.get('S3_URL')

# Blueprint 설정
fitness_bp = Blueprint('fitness', __name__, url_prefix='/fitness')

# 데이터 파일 경로 
STANDARD_DATA_PATH = "/Users/jangdabin/Documents/dev/youfit/youfit-flask-server/data/standard_data.json"
STD_DEVIATION_PATH = "/Users/jangdabin/Documents/dev/youfit/youfit-flask-server/data/std_deviation.json"
DATA_PATH_MEASURE = "/Users/jangdabin/Documents/dev/youfit/youfit-flask-server/data/measure.csv"
DATA_PATH_MEASURE_PERCENT = "/Users/jangdabin/Documents/dev/youfit/youfit-flask-server/data/measure_percent.csv"


# JSON 데이터 로드
with open(STANDARD_DATA_PATH, "r") as f:
    standard_data = json.load(f)

with open(STD_DEVIATION_PATH, "r") as f:
    std_deviation = json.load(f)

measure = pd.read_csv(DATA_PATH_MEASURE) 
measure_percent = pd.read_csv(DATA_PATH_MEASURE_PERCENT) 

# 백분위수 계산 함수
def safe_percentileofscore(data, value):
    valid_data = [x for x in data if x is not None and not np.isnan(x)]
    if len(valid_data) == 0:
        return None
    return percentileofscore(valid_data, value, kind='rank')

def get_user_percentages_and_dates(userId):
    results = (
        db.session.query(FitnessResult.percent, Fitness.date)
        .join(Fitness, FitnessResult.fitness_id == Fitness.fitness_id)
        .filter(Fitness.user_id == userId)
        .order_by(Fitness.fitness_id)  
        .limit(5)  # 최근 5개 가져오기
        .all()
    )

    data = [{"percent": result[0], "date": result[1]} for result in results]

    return data

def plot_distribution_with_input(data, userId, fitness_id, column_name, input_value, gender_column="성별구분코드", gender_filter="M"):
    plt.figure(figsize=(8, 5))
    subset = data[data[gender_column] == gender_filter]

    sns.histplot(subset[column_name], bins=range(0, 101, 5), color="#FFE45E", kde=False)
    plt.axvline(input_value, color='#FF6392', linestyle='--', linewidth=3, label=f"My rank: {input_value:.2f}%")
  
    plt.xlabel("Percentage")
    plt.xlim(0, 100)  
    plt.ylabel("Count")
    plt.legend()

    # 그래프를 이미지로 변환
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_binary = buffer.read()
    buffer.close()
    plt.close()  # plt 객체 닫기

    s3_file_path = f'graph/{userId}/{fitness_id}/{column_name}'
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    s3_client.put_object(Bucket=bucket_name, Key=s3_file_path, Body=image_binary, ContentType='image/png')

    # S3 URL 반환
    s3_image_url = f"https://{s3_url}/{s3_file_path}"
    
    return s3_image_url

# 그래프 변환후 s3에 저장
def get_line_chart(data, userId, fitness_id, file_name="chart.png"):
    # 날짜별 평균 percent 계산
    aggregated_data = defaultdict(list)
    for entry in data:
         # percent 값을 숫자로 변환
        percent_value = float(entry['percent'])
        aggregated_data[entry['date']].append(percent_value)

    dates = list(aggregated_data.keys())
    average_percent = [sum(values) / len(values) for values in aggregated_data.values()]

    # 라인차트 그리기
    plt.figure(figsize=(8, 5))
    plt.plot(dates, average_percent, marker='o', linestyle='-', linewidth=2)

    # 라벨 설정
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Percent (%)", fontsize=12)

    plt.ylim(0, 100)
    plt.xticks(rotation=0)
    plt.grid(True)

    # 그래프를 이미지로 변환
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_binary = buffer.read()
    buffer.close()
    plt.close()

    s3_file_path = f'change_chart/{userId}/{fitness_id}'
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    s3_client.put_object(Bucket=bucket_name, Key=s3_file_path, Body=image_binary, ContentType='image/png')

    # S3 URL 반환
    s3_image_url = f"https://{s3_url}/{s3_file_path}/{file_name}"
    
    return s3_image_url

# 운동 추천 함수
def recommend_exercises(items, mapping, data):
    recommendations = {}
    for item in items:
        for category, columns in mapping.items():
            if item in columns:
                exercise, link = random.choice(list(data[category].items()))
                recommendations[exercise] = link
    print(recommendations)           
    return recommendations

def save_exercises(recommendations, fitness_result_id):
    try:
        for name, url in recommendations.items():
            # Exercise 데이터 저장
            new_exercise = Exercise(
                exercise_name=name,
                exercise_url=url,
                fitness_result_id=fitness_result_id,
            )
            db.session.add(new_exercise)

        # 데이터베이스에 반영
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


@fitness_bp.route('/<int:userId>', methods=['POST'])
def analyze_fitness(userId):
    try:
        input_data = request.get_json()

        # 0. User 테이블에서 gender 가져오기
        user = db.session.query(User).filter(User.user_id == userId).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        gender = user.gender  # User 테이블에서 gender 값 가져오기
        print(gender)

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

        # fitness_id 및 date 가져오기
        fitness_id = fitness_entry.fitness_id
        date = fitness_entry.date

        # 2. 입력 데이터 분석
        # 그룹화 항목 처리
        group_pairs = {
            "20_run_treadmil": ("20_run", "treadmil_step"),
            "10_run_reaction": ("10_run", "reaction"),
            "long_jump_flight": ("long_jump", "flight_time")
        }

        # 분석 결과 저장
        percentile_scores = {}

        # 그룹 항목 분석
        for group, (col1, col2) in group_pairs.items():
            chosen_col = col1 if input_data.get(col1) is not None else col2
            value = input_data.get(chosen_col, None)
            if value is not None:
                percentile = safe_percentileofscore(measure[chosen_col], value)
                if percentile is not None:
                    top_percent = 100 - percentile
                    percentile_scores[chosen_col] = top_percent

        # 개별 항목 분석
        for col in ["grip_strength", "sit_up", "bend_forward"]:
            value = input_data.get(col, None)
            if value is not None:
                percentile = safe_percentileofscore(measure[col], value)
                if percentile is not None:
                    top_percent = 100 - percentile
                    percentile_scores[col] = top_percent

        # 평균 백분위 계산
        numeric_values = [value for value in percentile_scores.values() if isinstance(value, (int, float))]
        percent = int(np.mean(numeric_values)) if numeric_values else None

        # 그룹화 항목 처리
        group_pairs = {
            "cardio": ("20_run", "treadmil_step"),
            "agility": ("10_run", "reaction"),
            "power": ("long_jump", "flight_time")
        }

        graph_urls = []

        # 그룹 항목 처리 및 시각화
        for group, (col1, col2) in group_pairs.items():
            measure_percent[group] = measure_percent[[col1, col2]].clip(upper=100).max(axis=1)
            chosen_input_value = percentile_scores[col1] if not np.isnan(percentile_scores[col1]) else percentile_scores[col2]

            # 성별 필터링 값 가져오기 (M 또는 F)
            gender_filter = percentile_scores.get("성별구분코드", "M")  # 기본값 M, 없으면 M으로 처리

            url = plot_distribution_with_input(measure_percent, userId, fitness_id, group, chosen_input_value, gender_filter=gender_filter)
            graph_urls.append(url)

        # 개별 항목 처리 및 시각화
        individual_columns = ["grip_strength", "sit_up", "bend_forward"]
        for col in individual_columns:
            chosen_input_value = percentile_scores[col]

            # 성별 필터링 값 가져오기 (M 또는 F)
            gender_filter = percentile_scores.get("성별구분코드", "M")  # 기본값 M, 없으면 M으로 처리

            url = plot_distribution_with_input(measure_percent, userId, fitness_id, col, chosen_input_value, gender_filter=gender_filter)
            graph_urls.append(url)  # 입력값 그대로 사용

        # userId 에 해당하는 백분위 및 날짜 가져오기 -> 그래프 만들 때 필요
        data = get_user_percentages_and_dates(userId)
        new_entry = {"percent": percent, "date": input_data.get('date')}
        data.append(new_entry) # 새로 측정한 결과 추가

        change_chart_image_url = get_line_chart(data, userId, fitness_id)

        # 3. DB에 FitnessResult 저장
        fitness_result = FitnessResult(
            percent=percent,
            cardio=graph_urls[0],
            agility=graph_urls[1],
            power=graph_urls[2], 
            muscular_strength=graph_urls[3],
            muscular_endurance=graph_urls[4],
            flexibility=graph_urls[5],
            change_chart=change_chart_image_url,
            fitness_id=fitness_id
        )
        db.session.add(fitness_result)
        db.session.flush()  # fitness_result_id를 가져오기 위해 flush 호출

        fitness_result_id = fitness_result.fitness_result_id

        # 4. 운동 추천
        # Z-Score 계산
        z_scores = {}
        for key, value in input_data.items():
            if key in measure.columns and key in standard_data and key in std_deviation:
                z_scores[key] = (value - standard_data[key]) / std_deviation[key]

        # 차이가 큰 항목 3개 추출
        top_3_diff = sorted(z_scores.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        top_3_columns = [item[0] for item in top_3_diff]

        # 운동 추천
        recommendations = recommend_exercises(top_3_columns, category_mapping, exercise_data)

        # Exercise 테이블에 저장
        save_exercises(recommendations, fitness_result_id)

        exercises = [
            {"exerciseName": name, "exerciseUrl": url}
            for name, url in recommendations.items()
        ]

        db.session.commit()
        
        # 결과 반환 -> 그래프들 추가해야함
        return jsonify({
            "fitnessId": fitness_id,
            "percent": fitness_result.percent,
            "cardio": graph_urls[0],
            "agility": graph_urls[1],
            "power": graph_urls[2], 
            "muscular_strength": graph_urls[3],
            "muscular_endurance": graph_urls[4],
            "flexibility": graph_urls[5],
            "exercise": exercises
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500