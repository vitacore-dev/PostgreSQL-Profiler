# PostgreSQL Profiler Backend Dockerfile
FROM python:3.11-slim

# Метаданные
LABEL maintainer="Manus AI"
LABEL description="PostgreSQL Profiler Backend Service"
LABEL version="1.0"

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    FLASK_APP=src/main.py \
    FLASK_ENV=production

# Создание рабочей директории
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создание пользователя для безопасности
RUN groupadd -r appgroup && useradd -r -g appgroup -u 1000 appuser

# Копирование и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY src/ ./src/
COPY start.sh ./

# Создание директории для Celery Beat с правильными правами
RUN mkdir -p /app/celerybeat-schedule && \
    mkdir -p /app/logs && \
    mkdir -p /app/ml_models && \
    chmod 755 /app/celerybeat-schedule && \
    chmod 755 /app/logs && \
    chmod 755 /app/ml_models

# Установка прав доступа
RUN chmod +x start.sh && \
    chown -R appuser:appgroup /app

# Переключение на непривилегированного пользователя
USER appuser

# Открытие порта
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Команда запуска
CMD ["./start.sh"]

