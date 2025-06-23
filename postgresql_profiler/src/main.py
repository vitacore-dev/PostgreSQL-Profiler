# Обновленное главное приложение с интеграцией всех улучшений
import os
import time
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from celery import Celery
import redis
import structlog
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Импорты наших сервисов
from services.cache_service import CacheService, cache_response
from services.async_processing import AsyncTaskManager
from services.health_monitoring import HealthMonitor
from services.prometheus_metrics import PrometheusMetrics
from services.structured_logging import init_logging, get_logger, log_function_call
from models.profiler import db, DatabaseConnection, DatabaseMetric, Alert, Recommendation

# =====================================================
# КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ
# =====================================================

def create_app(config_name: str = 'development') -> Flask:
    """Фабрика приложений Flask с полной интеграцией улучшений"""
    
    app = Flask(__name__)
    
    # Загрузка конфигурации
    app.config.from_object(f'config.{config_name.title()}Config')
    
    # Инициализация расширений
    CORS(app, 
         origins=["*"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         supports_credentials=True)
    db.init_app(app)
    Migrate(app, db)
    
    # Инициализация системы логирования
    init_logging(app)
    logger = get_logger("app")
    
    # Инициализация Redis
    redis_client = redis.Redis.from_url(app.config['REDIS_URL'])
    app.redis = redis_client
    
    # Инициализация сервисов
    app.cache_service = CacheService(redis_client)
    app.health_monitor = HealthMonitor(app)
    app.metrics = PrometheusMetrics()
    app.async_manager = AsyncTaskManager(app)
    
    logger.info("Приложение инициализировано", config=config_name)
    
    # Регистрация middleware
    register_middleware(app)
    
    # Регистрация маршрутов
    register_routes(app)
    
    # Регистрация Blueprint маршрутов
    from routes.profiler import profiler_bp
    app.register_blueprint(profiler_bp, url_prefix='/api')
    
    # Регистрация обработчиков ошибок
    register_error_handlers(app)
    
    return app

def register_middleware(app: Flask):
    """Регистрация middleware для мониторинга и метрик"""
    
    @app.before_request
    def before_request():
        """Обработчик перед запросом"""
        g.start_time = time.time()
        
        # Увеличиваем счетчик запросов
        app.metrics.http_requests_total.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown'
        ).inc()
    
    @app.after_request
    def after_request(response):
        """Обработчик после запроса"""
        duration = time.time() - g.start_time
        
        # Записываем время ответа
        app.metrics.http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown',
            status_code=response.status_code
        ).observe(duration)
        
        # Добавляем заголовки CORS и безопасности
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response

def register_routes(app: Flask):
    """Регистрация всех маршрутов приложения"""
    
    # =====================================================
    # ОСНОВНЫЕ API МАРШРУТЫ
    # =====================================================
    
    @app.route('/api/health')
    @log_function_call
    def health_check():
        """Комплексная проверка здоровья системы"""
        health_status = app.health_monitor.get_comprehensive_health()
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
    
    @app.route('/api/metrics')
    def metrics_endpoint():
        """Endpoint для метрик Prometheus"""
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
    
    @app.route('/api/databases', methods=['GET', 'OPTIONS'])
    @cache_response  # Кэшируем на 5 минут
    @log_function_call
    def get_databases():
        """Получение списка сохраненных баз данных"""
        if request.method == 'OPTIONS':
            # Обработка preflight запроса
            response = jsonify({'status': 'ok'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
            return response
            
        try:
            databases = DatabaseConnection.query.filter_by(is_active=True).all()
            
            result = []
            for db_conn in databases:
                result.append({
                    'id': db_conn.id,
                    'name': db_conn.name,
                    'host': db_conn.host,
                    'port': db_conn.port,
                    'database': db_conn.database,
                    'status': db_conn.status,
                    'created_at': db_conn.created_at.isoformat(),
                    'last_check': db_conn.last_check.isoformat() if db_conn.last_check else None
                })
            
            app.metrics.database_connections_total.set(len(result))
            
            return jsonify({
                'success': True,
                'data': result,
                'total': len(result)
            })
            
        except Exception as exc:
            logger = get_logger("api")
            logger.error("Ошибка при получении списка баз данных", error=str(exc))
            
            return jsonify({
                'success': False,
                'error': 'Внутренняя ошибка сервера'
            }), 500
    
    @app.route('/api/databases', methods=['POST', 'OPTIONS'])
    @log_function_call
    def create_database_connection():
        """Создание нового соединения с базой данных"""
        if request.method == 'OPTIONS':
            # Обработка preflight запроса
            response = jsonify({'status': 'ok'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
            return response
            
        try:
            data = request.get_json()
            
            # Валидация данных
            required_fields = ['name', 'host', 'port', 'database', 'username', 'password']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Отсутствует обязательное поле: {field}'
                    }), 400
            
            # Создание нового соединения
            db_conn = DatabaseConnection(
                name=data['name'],
                host=data['host'],
                port=data['port'],
                database=data['database'],
                username=data['username'],
                password=data['password'],  # В реальном приложении нужно шифровать
                is_active=True
            )
            
            db.session.add(db_conn)
            db.session.commit()
            
            # Очищаем кэш списка баз данных
            app.cache_service.delete_pattern("get_databases:*")
            
            logger = get_logger("api")
            logger.info("Создано новое соединение с БД", database_id=db_conn.id, name=data['name'])
            
            return jsonify({
                'success': True,
                'data': {
                    'id': db_conn.id,
                    'name': db_conn.name,
                    'status': db_conn.status
                }
            }), 201
            
        except Exception as exc:
            db.session.rollback()
            logger = get_logger("api")
            logger.error("Ошибка при создании соединения с БД", error=str(exc))
            
            return jsonify({
                'success': False,
                'error': 'Ошибка при создании соединения'
            }), 500
    
    @app.route('/api/databases/<int:database_id>/metrics')
    @cache_response  # Кэшируем на 1 минуту
    @log_function_call
    def get_database_metrics(database_id: int):
        """Получение метрик базы данных с пагинацией"""
        try:
            # Параметры пагинации
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 50, type=int), 100)
            
            # Получение метрик с пагинацией
            metrics_query = DatabaseMetric.query.filter_by(database_id=database_id)
            metrics_paginated = metrics_query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            result = []
            for metric in metrics_paginated.items:
                result.append({
                    'id': metric.id,
                    'timestamp': metric.timestamp.isoformat(),
                    'cpu_usage': metric.cpu_usage,
                    'memory_usage': metric.memory_usage,
                    'disk_io': metric.disk_io,
                    'active_connections': metric.active_connections,
                    'query_count': metric.query_count,
                    'slow_queries': metric.slow_queries
                })
            
            return jsonify({
                'success': True,
                'data': result,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': metrics_paginated.total,
                    'pages': metrics_paginated.pages,
                    'has_next': metrics_paginated.has_next,
                    'has_prev': metrics_paginated.has_prev
                }
            })
            
        except Exception as exc:
            logger = get_logger("api")
            logger.error("Ошибка при получении метрик БД", database_id=database_id, error=str(exc))
            
            return jsonify({
                'success': False,
                'error': 'Ошибка при получении метрик'
            }), 500
    
    @app.route('/api/databases/<int:database_id>/analyze', methods=['POST'])
    @log_function_call
    def analyze_database_async(database_id: int):
        """Асинхронный анализ базы данных"""
        try:
            # Запускаем асинхронную задачу
            task = app.async_manager.start_database_analysis(database_id)
            
            return jsonify({
                'success': True,
                'task_id': task.id,
                'status': 'started',
                'message': 'Анализ базы данных запущен'
            }), 202
            
        except Exception as exc:
            logger = get_logger("api")
            logger.error("Ошибка при запуске анализа БД", database_id=database_id, error=str(exc))
            
            return jsonify({
                'success': False,
                'error': 'Ошибка при запуске анализа'
            }), 500
    
    @app.route('/api/tasks/<task_id>')
    @log_function_call
    def get_task_status(task_id: str):
        """Получение статуса асинхронной задачи"""
        try:
            task_info = app.async_manager.get_task_status(task_id)
            
            return jsonify({
                'success': True,
                'data': task_info
            })
            
        except Exception as exc:
            logger = get_logger("api")
            logger.error("Ошибка при получении статуса задачи", task_id=task_id, error=str(exc))
            
            return jsonify({
                'success': False,
                'error': 'Задача не найдена'
            }), 404
    
    @app.route('/api/alerts')
    @cache_response  # Кэшируем на 2 минуты
    @log_function_call
    def get_alerts():
        """Получение активных алертов с пагинацией"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            severity = request.args.get('severity')
            
            alerts_query = Alert.query.filter_by(is_active=True)
            
            if severity:
                alerts_query = alerts_query.filter_by(severity=severity)
            
            alerts_paginated = alerts_query.order_by(Alert.created_at.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            result = []
            for alert in alerts_paginated.items:
                result.append({
                    'id': alert.id,
                    'database_id': alert.database_id,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'message': alert.message,
                    'details': alert.details,
                    'created_at': alert.created_at.isoformat(),
                    'acknowledged': alert.acknowledged
                })
            
            # Обновляем метрики алертов
            app.metrics.active_alerts_total.labels(severity='critical').set(
                Alert.query.filter_by(is_active=True, severity='critical').count()
            )
            app.metrics.active_alerts_total.labels(severity='warning').set(
                Alert.query.filter_by(is_active=True, severity='warning').count()
            )
            
            return jsonify({
                'success': True,
                'data': result,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': alerts_paginated.total,
                    'pages': alerts_paginated.pages,
                    'has_next': alerts_paginated.has_next,
                    'has_prev': alerts_paginated.has_prev
                }
            })
            
        except Exception as exc:
            logger = get_logger("api")
            logger.error("Ошибка при получении алертов", error=str(exc))
            
            return jsonify({
                'success': False,
                'error': 'Ошибка при получении алертов'
            }), 500
    
    @app.route('/api/recommendations')
    @cache_response  # Кэшируем на 5 минут
    @log_function_call
    def get_recommendations():
        """Получение рекомендаций с пагинацией"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            category = request.args.get('category')
            
            recommendations_query = Recommendation.query.filter_by(is_active=True)
            
            if category:
                recommendations_query = recommendations_query.filter_by(category=category)
            
            recommendations_paginated = recommendations_query.order_by(
                Recommendation.priority.desc(),
                Recommendation.created_at.desc()
            ).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            result = []
            for rec in recommendations_paginated.items:
                result.append({
                    'id': rec.id,
                    'database_id': rec.database_id,
                    'category': rec.category,
                    'title': rec.title,
                    'description': rec.description,
                    'priority': rec.priority,
                    'impact': rec.impact,
                    'effort': rec.effort,
                    'created_at': rec.created_at.isoformat(),
                    'applied': rec.applied
                })
            
            return jsonify({
                'success': True,
                'data': result,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': recommendations_paginated.total,
                    'pages': recommendations_paginated.pages,
                    'has_next': recommendations_paginated.has_next,
                    'has_prev': recommendations_paginated.has_prev
                }
            })
            
        except Exception as exc:
            logger = get_logger("api")
            logger.error("Ошибка при получении рекомендаций", error=str(exc))
            
            return jsonify({
                'success': False,
                'error': 'Ошибка при получении рекомендаций'
            }), 500

def register_error_handlers(app: Flask):
    """Регистрация обработчиков ошибок"""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Ресурс не найден'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger = get_logger("error")
        logger.error("Внутренняя ошибка сервера", error=str(error))
        
        return jsonify({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger = get_logger("error")
        logger.error("Необработанная ошибка", error=str(error), error_type=type(error).__name__)
        
        return jsonify({
            'success': False,
            'error': 'Произошла неожиданная ошибка'
        }), 500

# =====================================================
# КОНФИГУРАЦИЯ CELERY
# =====================================================

def make_celery(app: Flask) -> Celery:
    """Создание и настройка Celery"""
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        """Задача с контекстом Flask приложения"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# =====================================================
# ТОЧКА ВХОДА
# =====================================================

# Создание приложения на уровне модуля для Gunicorn
app = create_app(os.getenv('FLASK_ENV', 'production'))

# Создание объекта celery на уровне модуля для Celery workers
celery = make_celery(app)

if __name__ == '__main__':
    # Создание таблиц базы данных
    with app.app_context():
        db.create_all()
    
    # Запуск приложения
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )

