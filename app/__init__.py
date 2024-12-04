from flask import Flask
from dotenv import load_dotenv
import os

def create_app():
    # 1. 환경변수 로드
    load_dotenv()

    # 2. Flask 애플리케이션 생성
    app = Flask(__name__)

    # 3. 환경변수에서 설정 로드
    app.config["DB_HOST"] = os.getenv("DB_HOST")
    app.config["DB_PORT"] = os.getenv("DB_PORT")
    app.config["DB_USER"] = os.getenv("DB_USER")
    app.config["DB_PASSWOR"] = os.getenv("DB_PASSWOR")
    app.config["DB_NAME"] = os.getenv("DB_NAME")

    return app