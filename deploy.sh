#!/bin/bash

# PostgreSQL Profiler - Улучшенный скрипт развертывания
set -e

echo "🚀 Starting PostgreSQL Profiler deployment..."

# Проверка зависимостей
check_dependencies() {
    echo "📋 Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    echo "✅ Dependencies check passed"
}

# Создание .env файла если не существует
setup_environment() {
    echo "🔧 Setting up environment..."
    
    if [ ! -f .env ]; then
        echo "📝 Creating .env file from template..."
        cp .env.example .env
        echo "⚠️  Please edit .env file with your configuration before continuing"
        echo "Press Enter to continue after editing .env file..."
        read
    fi
    
    # Загружаем переменные окружения
    source .env
    echo "✅ Environment setup completed"
}

# Создание необходимых директорий
create_directories() {
    echo "📁 Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p nginx/ssl
    
    echo "✅ Directories created"
}

# Сборка и запуск контейнеров
deploy_containers() {
    echo "🐳 Building and starting containers..."
    
    # Остановка существующих контейнеров
    echo "🛑 Stopping existing containers..."
    docker compose down --remove-orphans
    
    # Сборка образов
    echo "🔨 Building images..."
    docker compose build --no-cache
    
    # Запуск сервисов
    echo "🚀 Starting services..."
    docker compose up -d
    
    echo "✅ Containers deployed successfully"
}

# Проверка здоровья сервисов
check_health() {
    echo "🏥 Checking service health..."
    
    # Ожидание запуска сервисов
    echo "⏳ Waiting for services to start..."
    sleep 30
    
    # Проверка PostgreSQL
    echo "🔍 Checking PostgreSQL..."
    if docker compose exec -T postgres pg_isready -U ${POSTGRES_USER:-profiler} > /dev/null 2>&1; then
        echo "✅ PostgreSQL is healthy"
    else
        echo "❌ PostgreSQL is not responding"
        return 1
    fi
    
    # Проверка Redis
    echo "🔍 Checking Redis..."
    if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis is healthy"
    else
        echo "❌ Redis is not responding"
        return 1
    fi
    
    # Проверка Backend
    echo "🔍 Checking Backend API..."
    if curl -f http://localhost:${BACKEND_PORT:-5000}/api/health > /dev/null 2>&1; then
        echo "✅ Backend API is healthy"
    else
        echo "❌ Backend API is not responding"
        return 1
    fi
    
    # Проверка Frontend
    echo "🔍 Checking Frontend..."
    if curl -f http://localhost:${FRONTEND_PORT:-3000} > /dev/null 2>&1; then
        echo "✅ Frontend is healthy"
    else
        echo "❌ Frontend is not responding"
        return 1
    fi
    
    echo "✅ All services are healthy"
}

# Инициализация базы данных
initialize_database() {
    echo "🗃️ Initializing database..."
    
    # Ожидание готовности PostgreSQL
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 10
    
    # Выполнение миграций
    echo "🔄 Running database migrations..."
    docker compose exec backend python -c "
from src.main import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"
    
    echo "✅ Database initialized"
}

# Показ информации о развертывании
show_deployment_info() {
    echo ""
    echo "🎉 PostgreSQL Profiler deployed successfully!"
    echo ""
    echo "📊 Access URLs:"
    echo "   Frontend:  http://localhost:${FRONTEND_PORT:-3000}"
    echo "   Backend:   http://localhost:${BACKEND_PORT:-5000}"
    echo "   API Docs:  http://localhost:${BACKEND_PORT:-5000}/api/docs"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs:     docker compose logs -f"
    echo "   Stop services: docker compose down"
    echo "   Restart:       docker compose restart"
    echo ""
    echo "📁 Important directories:"
    echo "   Logs:     ./logs/"
    echo "   Data:     ./data/"
    echo "   Config:   ./.env"
    echo ""
}

# Основная функция
main() {
    echo "🔧 PostgreSQL Profiler Deployment Script"
    echo "========================================"
    
    check_dependencies
    setup_environment
    create_directories
    deploy_containers
    initialize_database
    check_health
    show_deployment_info
    
    echo "✅ Deployment completed successfully!"
}

# Обработка ошибок
handle_error() {
    echo ""
    echo "❌ Deployment failed!"
    echo "📋 Troubleshooting steps:"
    echo "   1. Check Docker logs: docker compose logs"
    echo "   2. Verify .env configuration"
    echo "   3. Ensure ports are not in use"
    echo "   4. Check system resources"
    echo ""
    echo "🔄 To retry deployment:"
    echo "   ./deploy.sh"
    echo ""
    exit 1
}

# Установка обработчика ошибок
trap handle_error ERR

# Запуск основной функции
main "$@"

