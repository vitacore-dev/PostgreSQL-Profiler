# PostgreSQL Profiler Frontend Dockerfile
FROM node:18-alpine as builder

# Метаданные
LABEL maintainer="Manus AI"
LABEL description="PostgreSQL Profiler Frontend Service"
LABEL version="1.0"

# Установка переменных окружения для сборки
ENV NODE_ENV=production
ENV GENERATE_SOURCEMAP=false

# Переменные окружения для API
ARG VITE_API_URL=http://localhost:5000/api
ENV VITE_API_URL=$VITE_API_URL

# Создание рабочей директории
WORKDIR /app

# Установка системных зависимостей
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++

# Копирование package файлов
COPY package*.json ./
COPY pnpm-lock.yaml* ./

# Установка pnpm и зависимостей
RUN npm install -g pnpm@latest && \
    pnpm install --frozen-lockfile --production=false

# Копирование исходного кода
COPY . .

# Сборка приложения
RUN pnpm build

# Production образ с Nginx
FROM nginx:1.25-alpine

# Метаданные для production образа
LABEL maintainer="Manus AI"
LABEL description="PostgreSQL Profiler Frontend (Production)"

# Установка дополнительных пакетов
RUN apk add --no-cache \
    curl \
    tzdata

# Создание пользователя для безопасности
RUN addgroup -g 1000 appgroup && \
    adduser -u 1000 -G appgroup -s /bin/sh -D appuser

# Копирование собранного приложения
COPY --from=builder /app/dist /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Создание директорий для логов, PID файлов и временных файлов nginx
RUN mkdir -p /var/log/nginx /var/cache/nginx /var/run \
             /tmp/client_body /tmp/proxy /tmp/fastcgi /tmp/uwsgi /tmp/scgi && \
    chown -R appuser:appgroup /var/log/nginx /var/cache/nginx /var/run /usr/share/nginx/html \
                              /tmp/client_body /tmp/proxy /tmp/fastcgi /tmp/uwsgi /tmp/scgi

# Копирование скрипта запуска
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Переключение на непривилегированного пользователя
USER appuser

# Открытие порта
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Команда запуска
CMD ["/start.sh"]

