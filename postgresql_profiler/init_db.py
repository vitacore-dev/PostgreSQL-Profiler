#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных PostgreSQL Profiler
"""
import os
import sys

# Добавляем src в путь поиска модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import create_app
from models.profiler import db, init_db

def init_database():
    """Инициализация базы данных"""
    # Создаем приложение
    app = create_app('development')
    
    with app.app_context():
        try:
            print("🔄 Создание таблиц базы данных...")
            
            # Удаляем все таблицы (осторожно в продакшене!)
            db.drop_all()
            
            # Создаем все таблицы
            db.create_all()
            
            print("✅ База данных успешно инициализирована!")
            print("📊 Таблицы созданы:")
            print("   - database_connection")
            print("   - database_metric")
            print("   - alert")
            print("   - recommendation")
            
        except Exception as e:
            print(f"❌ Ошибка при инициализации базы данных: {e}")
            sys.exit(1)

if __name__ == "__main__":
    init_database()
