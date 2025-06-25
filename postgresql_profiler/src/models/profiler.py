from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class DatabaseConnection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False, default=5432)
    database = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)  # В продакшене должно быть зашифровано
    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(50), default='unknown')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_check = db.Column(db.DateTime)

class DatabaseMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    database_id = db.Column(db.Integer, db.ForeignKey('database_connection.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    cpu_usage = db.Column(db.Float)
    memory_usage = db.Column(db.Float)
    disk_io = db.Column(db.Float)
    active_connections = db.Column(db.Integer)
    query_count = db.Column(db.Integer)
    slow_queries = db.Column(db.Integer)
    value = db.Column(db.Float, nullable=False)  # для обратной совместимости

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    database_id = db.Column(db.Integer, db.ForeignKey('database_connection.id'), nullable=False)
    alert_type = db.Column(db.String(100), nullable=False)
    severity = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    acknowledged = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    database_id = db.Column(db.Integer, db.ForeignKey('database_connection.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.Integer, default=1)
    impact = db.Column(db.String(50))
    effort = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    applied = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
