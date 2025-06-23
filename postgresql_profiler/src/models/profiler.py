from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class DatabaseConnection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class DatabaseMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float, nullable=False)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)

# Псевдоним для обратной совместимости
PerformanceMetric = DatabaseMetric

def init_db():
    """Инициализация базы данных"""
    try:
        db.create_all()
        print("✅ База данных инициализирована успешно")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации базы данных: {e}")
        # Не прерываем выполнение, так как таблицы могут уже существовать
