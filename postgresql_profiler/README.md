# PostgreSQL Profiler

Профессиональное решение для мониторинга и анализа производительности PostgreSQL баз данных с современным веб-интерфейсом и продвинутыми алгоритмами анализа.

## 🚀 Ключевые возможности

- **Мониторинг в реальном времени** - Непрерывный сбор и анализ метрик производительности
- **Интеллектуальный анализ запросов** - Автоматическая оптимизация и рекомендации
- **Обнаружение аномалий** - Машинное обучение для выявления проблем производительности
- **Система алертов** - Настраиваемые уведомления о критических событиях
- **Прогнозирование нагрузки** - Планирование мощности на основе исторических данных
- **RESTful API** - Полная интеграция с существующими системами мониторинга

## 🏗️ Архитектура

PostgreSQL Profiler построен на современном технологическом стеке:

### Backend
- **Flask** - Легковесный и гибкий веб-фреймворк
- **SQLAlchemy** - ORM для работы с базами данных
- **asyncpg** - Высокопроизводительный PostgreSQL драйвер
- **scikit-learn** - Машинное обучение для анализа данных
- **pandas/numpy** - Обработка и анализ временных рядов

### Frontend
- **React 18** - Современная библиотека для пользовательских интерфейсов
- **TypeScript** - Типизированный JavaScript для надежности
- **Vite** - Быстрая сборка и горячая перезагрузка
- **Tailwind CSS** - Utility-first CSS фреймворк
- **Chart.js** - Интерактивные графики и визуализации

## 📦 Быстрый старт

### Предварительные требования

- Python 3.11+
- Node.js 18+
- PostgreSQL 12+ (для мониторинга)

### Установка

1. **Клонирование репозитория**
```bash
git clone https://github.com/your-org/postgresql-profiler.git
cd postgresql-profiler
```

2. **Настройка Backend**
```bash
cd postgresql_profiler
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. **Настройка Frontend**
```bash
cd ../postgresql_profiler_frontend
npm install
# или
pnpm install
```

4. **Конфигурация**
```bash
# Создайте .env файл в директории backend
cp .env.example .env
# Отредактируйте .env с вашими настройками
```

5. **Запуск приложения**

Backend:
```bash
cd postgresql_profiler
source venv/bin/activate
python src/main.py
```

Frontend:
```bash
cd postgresql_profiler_frontend
npm run dev
# или
pnpm dev
```

6. **Доступ к приложению**
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000
- API документация: http://localhost:5000/api/docs

## 🔧 Конфигурация

### Переменные окружения

```bash
# База данных приложения
DATABASE_URL=sqlite:///profiler.db
# или для PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost:5432/profiler

# Безопасность
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# Мониторинг
METRICS_COLLECTION_INTERVAL=60  # секунды
ALERT_CHECK_INTERVAL=30         # секунды
DATA_RETENTION_DAYS=90          # дни

# Производительность
DATABASE_POOL_SIZE=10
WORKER_PROCESSES=4
```

### Настройка подключений к PostgreSQL

Добавьте подключения к вашим PostgreSQL серверам через веб-интерфейс:

1. Перейдите в раздел "Database Connections"
2. Нажмите "Add Connection"
3. Заполните параметры подключения:
   - Host: адрес сервера PostgreSQL
   - Port: порт (обычно 5432)
   - Database: имя базы данных
   - Username/Password: учетные данные
4. Протестируйте подключение
5. Сохраните конфигурацию

## 📊 Использование

### Dashboard

Главная панель предоставляет обзор всех мониторируемых баз данных:
- Сводная статистика производительности
- Графики временных рядов ключевых метрик
- Список активных алертов
- Быстрый доступ к основным функциям

### Анализ запросов

Query Analyzer позволяет:
- Выполнять EXPLAIN ANALYZE для любых запросов
- Получать рекомендации по оптимизации
- Сохранять часто используемые запросы
- Сравнивать производительность различных версий запросов

### Метрики производительности

Система собирает и анализирует:
- CPU и память сервера базы данных
- Статистику выполнения запросов
- Использование индексов
- Блокировки и ожидания
- Статистику ввода-вывода
- Размеры таблиц и индексов

### Система алертов

Настраиваемые алерты для:
- Превышения пороговых значений метрик
- Обнаружения аномалий в производительности
- Длительно выполняющихся запросов
- Проблем с подключениями
- Нехватки дискового пространства

## 🔌 API

PostgreSQL Profiler предоставляет полнофункциональный REST API:

```bash
# Получение списка подключений
GET /api/databases

# Добавление нового подключения
POST /api/databases
{
  "name": "Production DB",
  "host": "prod-db.example.com",
  "port": 5432,
  "database": "myapp",
  "username": "monitor",
  "password": "secret"
}

# Получение метрик производительности
GET /api/metrics/{database_id}?from=2024-01-01&to=2024-01-02

# Анализ SQL запроса
POST /api/queries/analyze
{
  "database_id": 1,
  "query": "SELECT * FROM users WHERE created_at > NOW() - INTERVAL '1 day'"
}
```

Полная API документация доступна по адресу `/api/docs` после запуска приложения.

## 🐳 Docker развертывание

Для быстрого развертывания используйте Docker Compose:

```bash
# Клонирование и запуск
git clone https://github.com/your-org/postgresql-profiler.git
cd postgresql-profiler
docker-compose up -d

# Приложение будет доступно по адресу http://localhost:3000
```

## 🧪 Тестирование

```bash
# Backend тесты
cd postgresql_profiler
source venv/bin/activate
pytest tests/

# Frontend тесты
cd postgresql_profiler_frontend
npm test
# или
pnpm test

# E2E тесты
npm run test:e2e
```

## 📈 Производительность

PostgreSQL Profiler оптимизирован для высокой производительности:

- **Асинхронный сбор метрик** - Неблокирующие операции с базой данных
- **Эффективное кэширование** - Redis для часто запрашиваемых данных
- **Пакетная обработка** - Группировка операций для снижения нагрузки
- **Сжатие данных** - Оптимизация хранения исторических метрик
- **Индексирование** - Оптимизированные индексы для быстрых запросов

Система способна мониторить сотни PostgreSQL серверов с минимальным влиянием на их производительность.

## 🔒 Безопасность

- **JWT аутентификация** - Безопасная аутентификация пользователей
- **Ролевая авторизация** - Гранулярные разрешения доступа
- **Шифрование паролей** - Безопасное хранение учетных данных
- **HTTPS поддержка** - Шифрование трафика
- **Аудит действий** - Логирование всех операций пользователей

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие PostgreSQL Profiler! Пожалуйста:

1. Форкните репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🆘 Поддержка

- **Документация**: [docs.postgresql-profiler.com](https://docs.postgresql-profiler.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/postgresql-profiler/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/postgresql-profiler/discussions)
- **Email**: support@postgresql-profiler.com

## 🗺️ Roadmap

### v2.0 (Q2 2024)
- [ ] Поддержка кластеров PostgreSQL
- [ ] Интеграция с Prometheus/Grafana
- [ ] Мобильное приложение
- [ ] Расширенная система алертов

### v2.1 (Q3 2024)
- [ ] Поддержка других СУБД (MySQL, MongoDB)
- [ ] Машинное обучение для автоматической оптимизации
- [ ] Интеграция с облачными провайдерами
- [ ] Система рекомендаций на основе ИИ

---

**PostgreSQL Profiler** - Ваш надежный партнер в обеспечении высокой производительности PostgreSQL баз данных! 🚀

