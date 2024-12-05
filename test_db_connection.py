from app import create_app, db
from sqlalchemy import text

def test_database_connection():
    """데이터베이스 연결 테스트"""
    app = create_app()

    with app.app_context():
        try:
            # Connection 객체 생성
            with db.engine.connect() as connection:
                result = connection.execute(text('SELECT 1')).fetchone()  # `text`로 감싸기
                if result[0] == 1:
                    print("Database connection successful!")
                else:
                    print("Database connection failed!")
        except Exception as e:
            print(f"Database connection error: {e}")

if __name__ == "__main__":
    test_database_connection()