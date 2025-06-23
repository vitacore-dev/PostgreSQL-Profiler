# Конфигурация Celery с оптимизированным расписанием для ML-задач
import os
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

def make_celery(app):
    """
    Создание и настройка Celery приложения
    """
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    
    # Обновление конфигурации Celery
    celery.conf.update(
        # Основные настройки
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        
        # Настройки производительности
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        worker_max_tasks_per_child=1000,
        
        # Настройки результатов
        result_expires=3600,
        result_backend_transport_options={
            'master_name': 'mymaster',
            'visibility_timeout': 3600,
        },
        
        # Настройки маршрутизации
        task_routes={
            'postgresql_profiler.services.ml_tasks.*': {'queue': 'ml_tasks'},
            'postgresql_profiler.services.celery_tasks.*': {'queue': 'monitoring'},
        },
        
        # Расписание периодических задач
        beat_schedule={
            # Обучение ML-моделей каждый час
            'train-load-predictor-hourly': {
                'task': 'postgresql_profiler.services.ml_tasks.train_load_predictor',
                'schedule': crontab(minute=0, hour='*'),  # каждый час
                'options': {'queue': 'ml_tasks'}
            },
            
            # Обучение детектора аномалий каждые 2 часа
            'train-anomaly-detector': {
                'task': 'postgresql_profiler.services.ml_tasks.train_anomaly_detector',
                'schedule': crontab(minute=30, hour='*/2'),  # каждые 2 часа в :30
                'options': {'queue': 'ml_tasks'}
            },
            
            # Обучение предиктора времени запросов каждые 3 часа
            'train-query-time-predictor': {
                'task': 'postgresql_profiler.services.ml_tasks.train_query_time_predictor',
                'schedule': crontab(minute=15, hour='*/3'),  # каждые 3 часа в :15
                'options': {'queue': 'ml_tasks'}
            },
            
            # Полное обучение всех моделей раз в день
            'train-all-models-daily': {
                'task': 'postgresql_profiler.services.ml_tasks.train_all_models',
                'schedule': crontab(minute=0, hour=2),  # каждый день в 02:00
                'options': {'queue': 'ml_tasks'}
            },
            
            # Очистка старых моделей раз в неделю
            'cleanup-old-models-weekly': {
                'task': 'postgresql_profiler.services.ml_tasks.cleanup_old_models',
                'schedule': crontab(minute=0, hour=3, day_of_week=0),  # воскресенье в 03:00
                'options': {'queue': 'ml_tasks'}
            },
            
            # Сбор метрик каждые 30 секунд
            'collect-metrics': {
                'task': 'postgresql_profiler.services.celery_tasks.collect_all_metrics',
                'schedule': timedelta(seconds=30),
                'options': {'queue': 'monitoring'}
            },
            
            # Анализ производительности каждые 5 минут
            'analyze-performance': {
                'task': 'postgresql_profiler.services.celery_tasks.analyze_performance_all_databases',
                'schedule': crontab(minute='*/5'),  # каждые 5 минут
                'options': {'queue': 'monitoring'}
            },
            
            # Проверка алертов каждую минуту
            'check-alerts': {
                'task': 'postgresql_profiler.services.celery_tasks.check_alerts_all_databases',
                'schedule': crontab(minute='*'),  # каждую минуту
                'options': {'queue': 'monitoring'}
            },
            
            # Генерация рекомендаций каждые 15 минут
            'generate-recommendations': {
                'task': 'postgresql_profiler.services.celery_tasks.generate_recommendations_all_databases',
                'schedule': crontab(minute='*/15'),  # каждые 15 минут
                'options': {'queue': 'monitoring'}
            },
            
            # Очистка старых метрик каждый день
            'cleanup-old-metrics': {
                'task': 'postgresql_profiler.services.celery_tasks.cleanup_old_metrics',
                'schedule': crontab(minute=30, hour=1),  # каждый день в 01:30
                'options': {'queue': 'monitoring'}
            },
            
            # Проверка здоровья системы каждые 10 минут
            'health-check': {
                'task': 'postgresql_profiler.services.celery_tasks.system_health_check',
                'schedule': crontab(minute='*/10'),  # каждые 10 минут
                'options': {'queue': 'monitoring'}
            }
        }
    )
    
    class ContextTask(celery.Task):
        """Обеспечивает контекст Flask приложения для задач"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Дополнительные настройки для production
CELERY_CONFIG = {
    # Настройки брокера
    'broker_url': os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    'result_backend': os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    
    # Настройки подключения к Redis
    'broker_connection_retry_on_startup': True,
    'broker_connection_retry': True,
    'broker_connection_max_retries': 10,
    
    # Настройки задач
    'task_always_eager': False,
    'task_eager_propagates': True,
    'task_ignore_result': False,
    'task_store_eager_result': True,
    
    # Настройки воркеров
    'worker_send_task_events': True,
    'worker_prefetch_multiplier': 1,
    'worker_max_tasks_per_child': 1000,
    'worker_disable_rate_limits': False,
    
    # Настройки мониторинга
    'task_send_sent_event': True,
    'task_track_started': True,
    'task_time_limit': 300,  # 5 минут
    'task_soft_time_limit': 240,  # 4 минуты
    
    # Настройки безопасности
    'worker_hijack_root_logger': False,
    'worker_log_color': False,
    
    # Настройки сериализации
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json'],
    
    # Настройки часового пояса
    'timezone': 'UTC',
    'enable_utc': True,
}

# Конфигурация для разных сред
class CeleryConfig:
    """Базовая конфигурация Celery"""
    
    # Основные настройки
    broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Настройки задач
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'UTC'
    enable_utc = True
    
    # Настройки производительности
    worker_prefetch_multiplier = 1
    task_acks_late = True
    worker_max_tasks_per_child = 1000
    
    # Настройки результатов
    result_expires = 3600
    task_ignore_result = False
    
    # Настройки мониторинга
    worker_send_task_events = True
    task_send_sent_event = True
    task_track_started = True
    
    # Лимиты времени выполнения
    task_time_limit = 300  # 5 минут
    task_soft_time_limit = 240  # 4 минуты

class DevelopmentCeleryConfig(CeleryConfig):
    """Конфигурация для разработки"""
    
    # Более частое обучение для тестирования
    beat_schedule = {
        'train-load-predictor-dev': {
            'task': 'postgresql_profiler.services.ml_tasks.train_load_predictor',
            'schedule': crontab(minute='*/30'),  # каждые 30 минут
        },
        'collect-metrics-dev': {
            'task': 'postgresql_profiler.services.celery_tasks.collect_all_metrics',
            'schedule': timedelta(seconds=60),  # каждую минуту
        }
    }

class ProductionCeleryConfig(CeleryConfig):
    """Конфигурация для production"""
    
    # Оптимизированные настройки для production
    worker_concurrency = os.environ.get('CELERY_WORKER_CONCURRENCY', 4)
    worker_max_memory_per_child = 200000  # 200MB
    
    # Настройки надежности
    broker_connection_retry_on_startup = True
    broker_connection_retry = True
    broker_connection_max_retries = 10
    
    # Настройки логирования
    worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
    worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

class TestingCeleryConfig(CeleryConfig):
    """Конфигурация для тестирования"""
    
    # Синхронное выполнение для тестов
    task_always_eager = True
    task_eager_propagates = True
    broker_url = 'memory://'
    result_backend = 'cache+memory://'

# Выбор конфигурации в зависимости от окружения
def get_celery_config():
    """Получение конфигурации Celery в зависимости от окружения"""
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionCeleryConfig
    elif env == 'testing':
        return TestingCeleryConfig
    else:
        return DevelopmentCeleryConfig

