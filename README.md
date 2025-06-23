# PostgreSQL Profiler - Готовый пакет для развертывания

## 📋 Содержимое пакета

Данный пакет содержит все необходимые файлы для полного развертывания PostgreSQL Profiler:

### 🔧 Backend компоненты
- `postgresql_profiler/` - Основное приложение Flask
- `postgresql_profiler/src/` - Исходный код backend
- `postgresql_profiler/requirements.txt` - Python зависимости
- `postgresql_profiler/Dockerfile` - Docker образ backend
- `postgresql_profiler/start.sh` - Скрипт запуска backend
- `postgresql_profiler/README_BACKEND.md` - Документация backend

### 🎨 Frontend компоненты
- `postgresql_profiler_frontend/` - React приложение
- `postgresql_profiler_frontend/src/` - Исходный код frontend
- `postgresql_profiler_frontend/package.json` - Node.js зависимости
- `postgresql_profiler_frontend/Dockerfile` - Docker образ frontend
- `postgresql_profiler_frontend/nginx.conf` - Конфигурация Nginx
- `postgresql_profiler_frontend/start.sh` - Скрипт запуска frontend
- `postgresql_profiler_frontend/.env.example` - Пример переменных окружения
- `postgresql_profiler_frontend/README.md` - Документация frontend

### 🐳 Конфигурация развертывания
- `docker-compose.yml` - Основная конфигурация Docker Compose
- `deploy.sh` - Автоматический скрипт развертывания
- `init.sql` - Инициализация базы данных
- `nginx/nginx.conf` - Конфигурация Nginx для production

### 📚 Документация
- `DEPLOYMENT_GUIDE.md` - Комплексное руководство по развертыванию
- `postgresql_profiler_documentation.md` - Техническая документация системы

## 🚀 Быстрый старт

### Автоматическое развертывание
```bash
# 1. Клонируйте или распакуйте файлы проекта
# 2. Перейдите в директорию проекта
cd postgresql-profiler

# 3. Запустите автоматическое развертывание
./deploy.sh
```

### Ручное развертывание
```bash
# 1. Создайте файл .env с настройками
cp .env.example .env
nano .env

# 2. Настройте переменные окружения frontend
cd postgresql_profiler_frontend
cp .env.example .env.local
# Отредактируйте VITE_API_URL при необходимости
cd ..

# 3. Соберите и запустите контейнеры
docker-compose up -d

# 4. Проверьте статус сервисов
docker-compose ps
```

## 🔗 Доступ к системе

После успешного развертывания:
- **Web интерфейс**: http://localhost:3000
- **API Backend**: http://localhost:5000
- **API Документация**: http://localhost:5000/api/docs

## 📖 Дополнительная информация

Подробные инструкции по развертыванию, настройке и эксплуатации системы содержатся в файле `DEPLOYMENT_GUIDE.md`.

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose logs`
2. Убедитесь в соответствии системным требованиям
3. Обратитесь к разделу "Устранение неполадок" в руководстве

---
**PostgreSQL Profiler v1.0**  
Разработано Manus AI

