#!/bin/bash

# Скрипт сборки PostgreSQL Profiler Frontend для продакшена
# Автор: Manus AI
# Дата: 18 июня 2025

set -e

echo "🏗️ Сборка PostgreSQL Profiler Frontend для продакшена..."

# Проверяем наличие Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js не найден. Установите Node.js 18 или выше."
    exit 1
fi

# Проверяем наличие pnpm
if ! command -v pnpm &> /dev/null; then
    echo "📦 pnpm не найден. Устанавливаем pnpm..."
    npm install -g pnpm
fi

# Устанавливаем зависимости
echo "📚 Установка зависимостей..."
pnpm install

# Настраиваем переменные окружения для продакшена
if [ -z "$VITE_API_URL" ]; then
    export VITE_API_URL=http://localhost:5000
    echo "🔧 Установлена переменная VITE_API_URL=$VITE_API_URL"
fi

# Очищаем предыдущую сборку
if [ -d "dist" ]; then
    echo "🧹 Очистка предыдущей сборки..."
    rm -rf dist
fi

# Собираем проект
echo "🔨 Сборка проекта..."
pnpm build

# Проверяем результат сборки
if [ -d "dist" ]; then
    echo "✅ Сборка завершена успешно!"
    echo "📁 Файлы сборки находятся в директории: dist/"
    echo "📊 Размер сборки:"
    du -sh dist/
    echo ""
    echo "🚀 Для запуска продакшен версии используйте:"
    echo "   pnpm preview"
    echo ""
    echo "🐳 Для развертывания в Docker используйте:"
    echo "   docker build -t postgresql-profiler-frontend ."
else
    echo "❌ Ошибка при сборке проекта!"
    exit 1
fi

