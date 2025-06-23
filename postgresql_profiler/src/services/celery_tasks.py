# Celery конфигурация и задачи для PostgreSQL Profiler
from celery import Celery
import os
import asyncio
import logging
from datetime import datetime, timedelta
from src.models.profiler import (
    db, DatabaseConnection, PerformanceMetric, QueryStatistic, 
    Alert, Recommendation, redis_client
)
from src.services.postgresql_monitor import postgresql_monitor, ConnectionConfig
from src.services.performance_analyzer import PerformanceAnalyzer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание Celery приложения
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
        broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    )
    
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 минут
        task_soft_time_limit=25 * 60,  # 25 минут
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
    )
    
    class ContextTask(celery.Task):
        """Задача с контекстом Flask приложения"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Инициализация Celery (будет вызвана из main.py)
celery = None

def init_celery(app):
    global celery
    celery = make_celery(app)
    return celery

@celery.task(bind=True)
def collect_metrics_task(self, db_id):
    """Задача для сбора метрик производительности"""
    try:
        logger.info(f"Starting metrics collection for database {db_id}")
        
        # Получаем информацию о базе данных
        db_connection = DatabaseConnection.query.get(db_id)
        if not db_connection or not db_connection.is_active:
            logger.warning(f"Database {db_id} not found or inactive")
            return {'status': 'skipped', 'reason': 'database_inactive'}
        
        # Создаем конфигурацию подключения
        config = ConnectionConfig(
            host=db_connection.host,
            port=db_connection.port,
            database=db_connection.database,
            username=db_connection.username,
            password=db_connection.password_encrypted,
            ssl_mode=db_connection.ssl_mode
        )
        
        # Создаем event loop для асинхронных операций
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Проверяем/создаем пул соединений
            if db_id not in postgresql_monitor.connection_pools:
                pool_created = loop.run_until_complete(
                    postgresql_monitor.create_connection_pool(db_id, config)
                )
                if not pool_created:
                    logger.error(f"Failed to create connection pool for database {db_id}")
                    return {'status': 'error', 'reason': 'connection_pool_failed'}
            
            # Собираем метрики
            metrics = loop.run_until_complete(
                postgresql_monitor.collect_performance_metrics(db_id)
            )
            
            if metrics is None:
                logger.error(f"Failed to collect metrics for database {db_id}")
                return {'status': 'error', 'reason': 'metrics_collection_failed'}
            
            # Сохраняем метрики в базу данных
            metric_record = PerformanceMetric(
                database_id=db_id,
                timestamp=datetime.utcnow(),
                active_connections=metrics.get('active_connections'),
                idle_connections=metrics.get('idle_connections'),
                max_connections=metrics.get('max_connections'),
                connection_utilization=metrics.get('connection_utilization'),
                tps=metrics.get('tps'),
                qps=metrics.get('qps'),
                avg_query_time=metrics.get('avg_query_time'),
                slow_queries_count=metrics.get('slow_queries_count'),
                cpu_usage=metrics.get('cpu_usage'),
                memory_usage=metrics.get('memory_usage'),
                disk_usage=metrics.get('disk_usage'),
                locks_count=metrics.get('locks_count'),
                deadlocks_count=metrics.get('deadlocks_count'),
                waiting_locks=metrics.get('waiting_locks'),
                cache_hit_ratio=metrics.get('cache_hit_ratio'),
                buffer_cache_hit_ratio=metrics.get('buffer_cache_hit_ratio'),
                disk_reads=metrics.get('disk_reads'),
                disk_writes=metrics.get('disk_writes'),
                database_size=metrics.get('database_size')
            )
            
            db.session.add(metric_record)
            db.session.commit()
            
            # Обновляем статус подключения
            db_connection.connection_status = 'connected'
            db_connection.last_connected = datetime.utcnow()
            db.session.commit()
            
            # Кэшируем последние метрики
            cache_key = f"latest_metrics:{db_id}"
            redis_client.setex(cache_key, 300, str(metrics))  # 5 минут
            
            # Очищаем кэш дашборда
            redis_client.delete(f"dashboard:{db_id}")
            
            logger.info(f"Successfully collected metrics for database {db_id}")
            return {'status': 'success', 'metrics_count': len(metrics)}
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error collecting metrics for database {db_id}: {str(e)}")
        
        # Обновляем статус подключения при ошибке
        try:
            db_connection = DatabaseConnection.query.get(db_id)
            if db_connection:
                db_connection.connection_status = 'error'
                db.session.commit()
        except:
            pass
        
        return {'status': 'error', 'error': str(e)}

@celery.task(bind=True)
def collect_query_statistics_task(self, db_id):
    """Задача для сбора статистики запросов"""
    try:
        logger.info(f"Starting query statistics collection for database {db_id}")
        
        # Получаем информацию о базе данных
        db_connection = DatabaseConnection.query.get(db_id)
        if not db_connection or not db_connection.is_active:
            return {'status': 'skipped', 'reason': 'database_inactive'}
        
        # Создаем event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Собираем статистику запросов
            query_stats = loop.run_until_complete(
                postgresql_monitor.collect_query_statistics(db_id)
            )
            
            updated_count = 0
            new_count = 0
            
            # Обновляем или создаем записи статистики
            for stat in query_stats:
                existing = QueryStatistic.query.filter_by(
                    database_id=db_id,
                    query_hash=stat['query_hash']
                ).first()
                
                if existing:
                    # Обновляем существующую запись
                    existing.calls = stat['calls']
                    existing.total_time = stat['total_time']
                    existing.mean_time = stat['mean_time']
                    existing.min_time = stat['min_time']
                    existing.max_time = stat['max_time']
                    existing.rows_returned = stat['rows_returned']
                    existing.shared_blks_hit = stat['shared_blks_hit']
                    existing.shared_blks_read = stat['shared_blks_read']
                    existing.shared_blks_written = stat['shared_blks_written']
                    existing.last_seen = datetime.utcnow()
                    
                    # Классифицируем производительность запроса
                    if existing.mean_time > 1000:  # > 1 секунды
                        existing.performance_category = 'critical'
                    elif existing.mean_time > 500:  # > 500ms
                        existing.performance_category = 'slow'
                    elif existing.mean_time > 100:  # > 100ms
                        existing.performance_category = 'normal'
                    else:
                        existing.performance_category = 'fast'
                    
                    updated_count += 1
                else:
                    # Создаем новую запись
                    query_record = QueryStatistic(
                        database_id=db_id,
                        query_hash=stat['query_hash'],
                        query_text=stat['query_text'],
                        query_type=stat['query_type'],
                        calls=stat['calls'],
                        total_time=stat['total_time'],
                        mean_time=stat['mean_time'],
                        min_time=stat['min_time'],
                        max_time=stat['max_time'],
                        rows_returned=stat['rows_returned'],
                        shared_blks_hit=stat['shared_blks_hit'],
                        shared_blks_read=stat['shared_blks_read'],
                        shared_blks_written=stat['shared_blks_written']
                    )
                    
                    # Классифицируем производительность
                    if query_record.mean_time > 1000:
                        query_record.performance_category = 'critical'
                    elif query_record.mean_time > 500:
                        query_record.performance_category = 'slow'
                    elif query_record.mean_time > 100:
                        query_record.performance_category = 'normal'
                    else:
                        query_record.performance_category = 'fast'
                    
                    db.session.add(query_record)
                    new_count += 1
            
            db.session.commit()
            
            # Очищаем кэш запросов
            cache_pattern = f"queries:{db_id}:*"
            for key in redis_client.scan_iter(match=cache_pattern):
                redis_client.delete(key)
            
            logger.info(f"Query statistics updated for database {db_id}: {updated_count} updated, {new_count} new")
            return {
                'status': 'success', 
                'updated': updated_count, 
                'new': new_count
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error collecting query statistics for database {db_id}: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@celery.task(bind=True)
def analyze_performance_task(self, db_id):
    """Задача для анализа производительности и генерации алертов/рекомендаций"""
    try:
        logger.info(f"Starting performance analysis for database {db_id}")
        
        # Получаем информацию о базе данных
        db_connection = DatabaseConnection.query.get(db_id)
        if not db_connection or not db_connection.is_active:
            return {'status': 'skipped', 'reason': 'database_inactive'}
        
        # Инициализируем анализатор производительности
        analyzer = PerformanceAnalyzer()
        
        # Получаем последние метрики
        recent_metrics = PerformanceMetric.query.filter(
            PerformanceMetric.database_id == db_id,
            PerformanceMetric.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ).order_by(PerformanceMetric.timestamp.desc()).limit(60).all()
        
        if not recent_metrics:
            return {'status': 'skipped', 'reason': 'no_metrics'}
        
        # Анализируем метрики и генерируем алерты
        alerts_generated = analyzer.analyze_metrics_and_generate_alerts(
            db_id, recent_metrics, db_connection.alert_thresholds or {}
        )
        
        # Анализируем запросы и генерируем рекомендации
        slow_queries = QueryStatistic.query.filter(
            QueryStatistic.database_id == db_id,
            QueryStatistic.performance_category.in_(['slow', 'critical'])
        ).order_by(QueryStatistic.mean_time.desc()).limit(20).all()
        
        recommendations_generated = analyzer.analyze_queries_and_generate_recommendations(
            db_id, slow_queries
        )
        
        logger.info(f"Performance analysis completed for database {db_id}: "
                   f"{alerts_generated} alerts, {recommendations_generated} recommendations")
        
        return {
            'status': 'success',
            'alerts_generated': alerts_generated,
            'recommendations_generated': recommendations_generated
        }
        
    except Exception as e:
        logger.error(f"Error analyzing performance for database {db_id}: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@celery.task(bind=True)
def cleanup_old_data_task(self):
    """Задача для очистки старых данных"""
    try:
        logger.info("Starting cleanup of old data")
        
        # Удаляем метрики старше 30 дней
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_metrics = PerformanceMetric.query.filter(
            PerformanceMetric.timestamp < cutoff_date
        ).delete()
        
        # Удаляем разрешённые алерты старше 7 дней
        old_alerts = Alert.query.filter(
            Alert.is_resolved == True,
            Alert.resolved_at < datetime.utcnow() - timedelta(days=7)
        ).delete()
        
        # Удаляем применённые рекомендации старше 30 дней
        old_recommendations = Recommendation.query.filter(
            Recommendation.is_applied == True,
            Recommendation.applied_at < datetime.utcnow() - timedelta(days=30)
        ).delete()
        
        db.session.commit()
        
        logger.info(f"Cleanup completed: {old_metrics} metrics, {old_alerts} alerts, "
                   f"{old_recommendations} recommendations removed")
        
        return {
            'status': 'success',
            'metrics_removed': old_metrics,
            'alerts_removed': old_alerts,
            'recommendations_removed': old_recommendations
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@celery.task(bind=True)
def schedule_monitoring_tasks(self):
    """Планировщик задач мониторинга для всех активных баз данных"""
    try:
        logger.info("Scheduling monitoring tasks for all active databases")
        
        # Получаем все активные базы данных с включённым автомониторингом
        active_databases = DatabaseConnection.query.filter_by(
            is_active=True,
            auto_monitoring=True
        ).all()
        
        scheduled_count = 0
        
        for db_conn in active_databases:
            # Планируем сбор метрик
            collect_metrics_task.apply_async(
                args=[db_conn.id],
                countdown=0  # Выполнить немедленно
            )
            
            # Планируем сбор статистики запросов (каждые 5 минут)
            collect_query_statistics_task.apply_async(
                args=[db_conn.id],
                countdown=300  # Через 5 минут
            )
            
            # Планируем анализ производительности (каждые 10 минут)
            analyze_performance_task.apply_async(
                args=[db_conn.id],
                countdown=600  # Через 10 минут
            )
            
            scheduled_count += 1
        
        logger.info(f"Scheduled monitoring tasks for {scheduled_count} databases")
        
        return {
            'status': 'success',
            'databases_scheduled': scheduled_count
        }
        
    except Exception as e:
        logger.error(f"Error scheduling monitoring tasks: {str(e)}")
        return {'status': 'error', 'error': str(e)}

# Периодические задачи
from celery.schedules import crontab

celery.conf.beat_schedule = {
    # Планировщик мониторинга каждую минуту
    'schedule-monitoring': {
        'task': 'src.services.celery_tasks.schedule_monitoring_tasks',
        'schedule': crontab(minute='*'),  # Каждую минуту
    },
    
    # Очистка старых данных каждый день в 2:00
    'cleanup-old-data': {
        'task': 'src.services.celery_tasks.cleanup_old_data_task',
        'schedule': crontab(hour=2, minute=0),  # В 2:00 каждый день
    },
}

celery.conf.timezone = 'UTC'

