from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# 확장 초기화
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # .env 파일 로드
    load_dotenv()

    # 환경 변수 설정
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

    # 확장 초기화
    db.init_app(app)

    return app