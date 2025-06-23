#!/bin/bash

# PostgreSQL Profiler Backend Start Script
# Автор: Manus AI
# Версия: 1.0

set -e

echo "🚀 Запуск PostgreSQL Profiler Backend..."

# Проверка переменных окружения
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  Предупреждение: DATABASE_URL не установлен, используется значение по умолчанию"
    export DATABASE_URL="postgresql://profiler:profiler123@db:5432/profiler_db"
fi

if [ -z "$REDIS_URL" ]; then
    echo "⚠️  Предупреждение: REDIS_URL не установлен, используется значение по умолчанию"
    export REDIS_URL="redis://redis:6379/0"
fi

# Ожидание доступности базы данных
echo "⏳ Ожидание доступности PostgreSQL..."
while ! python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close()
    print('✅ PostgreSQL доступен')
except:
    print('❌ PostgreSQL недоступен')
    exit(1)
" 2>/dev/null; do
    echo "⏳ Ожидание PostgreSQL..."
    sleep 2
done

# Ожидание доступности Redis
echo "⏳ Ожидание доступности Redis..."
while ! python -c "
import redis
import os
try:
    r = redis.from_url(os.environ['REDIS_URL'])
    r.ping()
    print('✅ Redis доступен')
except:
    print('❌ Redis недоступен')
    exit(1)
" 2>/dev/null; do
    echo "⏳ Ожидание Redis..."
    sleep 2
done

# Инициализация базы данных
echo "🔧 Инициализация базы данных..."
python -c "
from src.models.profiler import init_db
init_db()
print('✅ База данных инициализирована')
" || echo "⚠️  База данных уже инициализирована"

# Запуск приложения
echo "🎯 Запуск Flask приложения..."
if [ "$FLASK_ENV" = "development" ]; then
    echo "🔧 Режим разработки"
    python src/main.py
else
    echo "🚀 Продакшен режим с Gunicorn"
    gunicorn --bind 0.0.0.0:5000 \
             --workers 4 \
             --worker-class gevent \
             --worker-connections 1000 \
             --timeout 120 \
             --keep-alive 5 \
             --max-requests 1000 \
             --max-requests-jitter 100 \
             --preload \
             --access-logfile - \
             --error-logfile - \
             --log-level info \
             src.main:app
fi

