#!/bin/sh

# PostgreSQL Profiler Frontend Start Script
# Автор: Manus AI
# Версия: 1.0

set -e

echo "🚀 Запуск PostgreSQL Profiler Frontend..."

# Проверка наличия собранных файлов
if [ ! -d "/usr/share/nginx/html" ] || [ -z "$(ls -A /usr/share/nginx/html)" ]; then
    echo "❌ Ошибка: Собранные файлы frontend не найдены"
    exit 1
fi

echo "✅ Файлы frontend найдены"

# Проверка конфигурации Nginx
echo "🔧 Проверка конфигурации Nginx..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Конфигурация Nginx корректна"
else
    echo "❌ Ошибка в конфигурации Nginx"
    exit 1
fi

# Создание необходимых директорий
mkdir -p /tmp/nginx/client_body
mkdir -p /tmp/nginx/proxy
mkdir -p /tmp/nginx/fastcgi
mkdir -p /tmp/nginx/uwsgi
mkdir -p /tmp/nginx/scgi

# Установка прав доступа
chmod 755 /tmp/nginx/*

echo "🎯 Запуск Nginx..."

# Запуск Nginx в foreground режиме
exec nginx -g "daemon off;"

