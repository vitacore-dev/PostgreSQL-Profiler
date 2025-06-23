#!/bin/bash

# PostgreSQL Profiler - Скрипт проверки готовности к сборке
# Автор: Manus AI
# Версия: 1.0

set -e

echo "🔍 Проверка готовности PostgreSQL Profiler к сборке..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Счетчики
ERRORS=0
WARNINGS=0

# Функция для вывода ошибок
error() {
    echo -e "${RED}❌ ОШИБКА: $1${NC}"
    ((ERRORS++))
}

# Функция для вывода предупреждений
warning() {
    echo -e "${YELLOW}⚠️  ПРЕДУПРЕЖДЕНИЕ: $1${NC}"
    ((WARNINGS++))
}

# Функция для вывода успеха
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Функция для вывода информации
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo "==========================================="
echo "🔍 ПРОВЕРКА СТРУКТУРЫ ПРОЕКТА"
echo "==========================================="

# Проверка основных директорий
if [ -d "postgresql_profiler" ]; then
    success "Директория backend найдена"
else
    error "Директория postgresql_profiler не найдена"
fi

if [ -d "postgresql_profiler_frontend" ]; then
    success "Директория frontend найдена"
else
    error "Директория postgresql_profiler_frontend не найдена"
fi

# Проверка основных файлов
if [ -f "docker-compose.yml" ]; then
    success "docker-compose.yml найден"
else
    error "docker-compose.yml не найден"
fi

if [ -f ".env.example" ]; then
    success ".env.example найден"
else
    error ".env.example не найден"
fi

echo ""
echo "==========================================="
echo "🔍 ПРОВЕРКА BACKEND КОМПОНЕНТОВ"
echo "==========================================="

# Проверка Dockerfile backend
if [ -f "postgresql_profiler/Dockerfile" ]; then
    success "Backend Dockerfile найден"
else
    error "Backend Dockerfile не найден"
fi

# Проверка requirements.txt
if [ -f "postgresql_profiler/requirements.txt" ]; then
    success "requirements.txt найден"
    
    # Проверка основных зависимостей
    if grep -q "Flask" postgresql_profiler/requirements.txt; then
        success "Flask зависимость найдена"
    else
        error "Flask зависимость не найдена в requirements.txt"
    fi
    
    if grep -q "celery" postgresql_profiler/requirements.txt; then
        success "Celery зависимость найдена"
    else
        error "Celery зависимость не найдена в requirements.txt"
    fi
    
    if grep -q "redis" postgresql_profiler/requirements.txt; then
        success "Redis зависимость найдена"
    else
        error "Redis зависимость не найдена в requirements.txt"
    fi
else
    error "requirements.txt не найден"
fi

# Проверка скрипта запуска
if [ -f "postgresql_profiler/start.sh" ]; then
    success "Backend start.sh найден"
    if [ -x "postgresql_profiler/start.sh" ]; then
        success "start.sh исполняемый"
    else
        warning "start.sh не исполняемый"
    fi
else
    error "Backend start.sh не найден"
fi

# Проверка основного файла приложения
if [ -f "postgresql_profiler/src/main.py" ]; then
    success "main.py найден"
else
    error "main.py не найден"
fi

echo ""
echo "==========================================="
echo "🔍 ПРОВЕРКА FRONTEND КОМПОНЕНТОВ"
echo "==========================================="

# Проверка Dockerfile frontend
if [ -f "postgresql_profiler_frontend/Dockerfile" ]; then
    success "Frontend Dockerfile найден"
else
    error "Frontend Dockerfile не найден"
fi

# Проверка package.json
if [ -f "postgresql_profiler_frontend/package.json" ]; then
    success "package.json найден"
    
    # Проверка основных зависимостей
    if grep -q "react" postgresql_profiler_frontend/package.json; then
        success "React зависимость найдена"
    else
        error "React зависимость не найдена в package.json"
    fi
    
    if grep -q "vite" postgresql_profiler_frontend/package.json; then
        success "Vite зависимость найдена"
    else
        error "Vite зависимость не найдена в package.json"
    fi
else
    error "package.json не найден"
fi

# Проверка nginx конфигурации
if [ -f "postgresql_profiler_frontend/nginx.conf" ]; then
    success "nginx.conf найден"
else
    error "nginx.conf не найден"
fi

# Проверка скрипта запуска frontend
if [ -f "postgresql_profiler_frontend/start.sh" ]; then
    success "Frontend start.sh найден"
    if [ -x "postgresql_profiler_frontend/start.sh" ]; then
        success "Frontend start.sh исполняемый"
    else
        warning "Frontend start.sh не исполняемый"
    fi
else
    error "Frontend start.sh не найден"
fi

echo ""
echo "==========================================="
echo "🔍 ПРОВЕРКА PYTHON КОДА"
echo "==========================================="

# Проверка синтаксиса Python файлов
info "Проверка синтаксиса Python файлов..."
PYTHON_ERRORS=0

if command -v python3 &> /dev/null; then
    while IFS= read -r -d '' file; do
        if ! python3 -m py_compile "$file" 2>/dev/null; then
            error "Синтаксическая ошибка в файле: $file"
            ((PYTHON_ERRORS++))
        fi
    done < <(find postgresql_profiler -name "*.py" -print0 2>/dev/null)
    
    if [ $PYTHON_ERRORS -eq 0 ]; then
        success "Все Python файлы прошли проверку синтаксиса"
    else
        error "Найдено $PYTHON_ERRORS файлов с синтаксическими ошибками"
    fi
else
    warning "Python3 не найден, пропускаем проверку синтаксиса"
fi

echo ""
echo "==========================================="
echo "🔍 ПРОВЕРКА КОНФИГУРАЦИОННЫХ ФАЙЛОВ"
echo "==========================================="

# Проверка docker-compose.yml
if command -v docker-compose &> /dev/null; then
    if docker-compose config &>/dev/null; then
        success "docker-compose.yml синтаксически корректен"
    else
        error "Ошибка в синтаксисе docker-compose.yml"
    fi
else
    warning "docker-compose не найден, пропускаем проверку"
fi

# Проверка nginx конфигурации
if command -v nginx &> /dev/null; then
    if nginx -t -c "$(pwd)/postgresql_profiler_frontend/nginx.conf" &>/dev/null; then
        success "nginx.conf синтаксически корректен"
    else
        warning "Возможные проблемы в nginx.conf (требует дополнительной проверки)"
    fi
else
    warning "nginx не найден, пропускаем проверку конфигурации"
fi

echo ""
echo "==========================================="
echo "📊 ИТОГОВЫЙ ОТЧЕТ"
echo "==========================================="

if [ $ERRORS -eq 0 ]; then
    success "Проект готов к сборке! Ошибок не найдено."
    if [ $WARNINGS -gt 0 ]; then
        warning "Найдено $WARNINGS предупреждений, но они не критичны"
    fi
    echo ""
    info "Для сборки выполните:"
    echo "  1. cp .env.example .env"
    echo "  2. Отредактируйте .env под ваши нужды"
    echo "  3. docker-compose up --build"
    echo ""
    exit 0
else
    error "Найдено $ERRORS критических ошибок!"
    error "Исправьте ошибки перед сборкой"
    echo ""
    exit 1
fi

