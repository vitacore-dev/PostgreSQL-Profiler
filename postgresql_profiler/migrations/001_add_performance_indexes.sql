-- Миграция для добавления индексов производительности PostgreSQL Profiler
-- Версия: 001_add_performance_indexes
-- Дата: 2024-12-20

-- =====================================================
-- АНАЛИЗ ТЕКУЩИХ ЗАПРОСОВ И НЕОБХОДИМЫХ ИНДЕКСОВ
-- =====================================================

/*
Анализ показал следующие критичные запросы:

1. Поиск метрик по database_id и временному диапазону
   SELECT * FROM database_metrics WHERE database_id = ? AND timestamp BETWEEN ? AND ?

2. Поиск последних метрик для дашборда
   SELECT * FROM database_metrics WHERE database_id = ? ORDER BY timestamp DESC LIMIT ?

3. Поиск алертов по приоритету и статусу
   SELECT * FROM alerts WHERE database_id = ? AND priority = ? AND status = ?

4. Поиск рекомендаций по типу
   SELECT * FROM recommendations WHERE database_id = ? AND recommendation_type = ?

5. Поиск соединений по статусу
   SELECT * FROM database_connections WHERE status = 'active'

6. Агрегация метрик по часам/дням
   SELECT DATE_TRUNC('hour', timestamp), AVG(cpu_usage) FROM database_metrics GROUP BY 1

7. Поиск медленных запросов
   SELECT * FROM query_statistics WHERE database_id = ? AND execution_time > ?
*/

-- =====================================================
-- СОЗДАНИЕ ИНДЕКСОВ ДЛЯ ТАБЛИЦЫ database_metrics
-- =====================================================

-- Композитный индекс для поиска метрик по БД и времени (самый критичный)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_database_metrics_db_timestamp 
ON database_metrics (database_id, timestamp DESC);

-- Индекс для быстрого поиска последних метрик
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_database_metrics_timestamp_desc 
ON database_metrics (timestamp DESC);

-- Индекс для поиска по database_id (если нужен отдельно)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_database_metrics_database_id 
ON database_metrics (database_id);

-- Частичный индекс для критичных метрик (высокая нагрузка)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_database_metrics_high_load 
ON database_metrics (database_id, timestamp DESC) 
WHERE cpu_usage > 80 OR memory_usage > 80 OR active_connections > 100;

-- Индекс для агрегации по времени
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_database_metrics_time_bucket 
ON database_metrics (database_id, DATE_TRUNC('hour', timestamp));

-- =====================================================
-- СОЗДАНИЕ ИНДЕКСОВ ДЛЯ ТАБЛИЦЫ alerts
-- =====================================================

-- Композитный индекс для поиска алертов
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_db_priority_status 
ON alerts (database_id, priority, status);

-- Индекс для поиска активных алертов
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_active 
ON alerts (database_id, created_at DESC) 
WHERE status = 'active';

-- Индекс для поиска по времени создания
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_created_at 
ON alerts (created_at DESC);

-- Индекс для поиска по типу алерта
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_type 
ON alerts (alert_type, database_id);

-- =====================================================
-- СОЗДАНИЕ ИНДЕКСОВ ДЛЯ ТАБЛИЦЫ recommendations
-- =====================================================

-- Композитный индекс для поиска рекомендаций
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recommendations_db_type 
ON recommendations (database_id, recommendation_type);

-- Индекс для поиска активных рекомендаций
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recommendations_active 
ON recommendations (database_id, created_at DESC) 
WHERE status = 'active';

-- Индекс для поиска по приоритету
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recommendations_priority 
ON recommendations (priority, database_id);

-- =====================================================
-- СОЗДАНИЕ ИНДЕКСОВ ДЛЯ ТАБЛИЦЫ database_connections
-- =====================================================

-- Индекс для поиска активных соединений
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_database_connections_status 
ON database_connections (status) 
WHERE status = 'active';

-- Индекс для поиска по пользователю
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_database_connections_user 
ON database_connections (created_by, status);

-- Индекс для поиска по времени создания
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_database_connections_created 
ON database_connections (created_at DESC);

-- =====================================================
-- СОЗДАНИЕ ИНДЕКСОВ ДЛЯ ТАБЛИЦЫ query_statistics
-- =====================================================

-- Композитный индекс для поиска медленных запросов
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_query_statistics_db_time 
ON query_statistics (database_id, execution_time DESC);

-- Индекс для поиска по времени выполнения
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_query_statistics_execution_time 
ON query_statistics (execution_time DESC) 
WHERE execution_time > 1000; -- медленные запросы > 1 сек

-- Индекс для поиска по query_hash (дедупликация)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_query_statistics_hash 
ON query_statistics (query_hash, database_id);

-- Индекс для поиска по времени записи
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_query_statistics_recorded 
ON query_statistics (recorded_at DESC);

-- =====================================================
-- СОЗДАНИЕ ИНДЕКСОВ ДЛЯ ТАБЛИЦЫ ml_models
-- =====================================================

-- Индекс для поиска моделей по БД и типу
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ml_models_db_type 
ON ml_models (database_id, model_type);

-- Индекс для поиска активных моделей
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ml_models_active 
ON ml_models (model_type, updated_at DESC) 
WHERE status = 'active';

-- =====================================================
-- СОЗДАНИЕ ИНДЕКСОВ ДЛЯ ТАБЛИЦЫ task_results
-- =====================================================

-- Индекс для поиска задач по статусу
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_results_status 
ON task_results (status, created_at DESC);

-- Индекс для поиска задач по типу
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_results_type 
ON task_results (task_type, database_id);

-- Индекс для поиска по task_id
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_results_task_id 
ON task_results (task_id);

-- =====================================================
-- АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ ИНДЕКСОВ
-- =====================================================

-- Функция для анализа использования индексов
CREATE OR REPLACE FUNCTION analyze_index_usage()
RETURNS TABLE (
    schemaname text,
    tablename text,
    indexname text,
    idx_scan bigint,
    idx_tup_read bigint,
    idx_tup_fetch bigint,
    usage_ratio numeric
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.schemaname,
        s.tablename,
        s.indexname,
        s.idx_scan,
        s.idx_tup_read,
        s.idx_tup_fetch,
        CASE 
            WHEN s.idx_scan = 0 THEN 0
            ELSE ROUND((s.idx_tup_fetch::numeric / s.idx_scan), 2)
        END as usage_ratio
    FROM pg_stat_user_indexes s
    JOIN pg_index i ON s.indexrelid = i.indexrelid
    WHERE s.schemaname = 'public'
    ORDER BY s.idx_scan DESC;
END;
$$ LANGUAGE plpgsql;

-- Функция для поиска неиспользуемых индексов
CREATE OR REPLACE FUNCTION find_unused_indexes()
RETURNS TABLE (
    schemaname text,
    tablename text,
    indexname text,
    index_size text
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.schemaname,
        s.tablename,
        s.indexname,
        pg_size_pretty(pg_relation_size(s.indexrelid)) as index_size
    FROM pg_stat_user_indexes s
    JOIN pg_index i ON s.indexrelid = i.indexrelid
    WHERE s.idx_scan = 0
    AND s.schemaname = 'public'
    AND NOT i.indisunique  -- исключаем уникальные индексы
    ORDER BY pg_relation_size(s.indexrelid) DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- МОНИТОРИНГ ПРОИЗВОДИТЕЛЬНОСТИ ЗАПРОСОВ
-- =====================================================

-- Включаем расширение pg_stat_statements если доступно
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Функция для анализа медленных запросов
CREATE OR REPLACE FUNCTION analyze_slow_queries(min_duration_ms integer DEFAULT 1000)
RETURNS TABLE (
    query text,
    calls bigint,
    total_time numeric,
    mean_time numeric,
    rows bigint,
    hit_percent numeric
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pss.query,
        pss.calls,
        ROUND(pss.total_exec_time::numeric, 2) as total_time,
        ROUND(pss.mean_exec_time::numeric, 2) as mean_time,
        pss.rows,
        ROUND(
            (pss.shared_blks_hit::numeric / 
             NULLIF(pss.shared_blks_hit + pss.shared_blks_read, 0)) * 100, 
            2
        ) as hit_percent
    FROM pg_stat_statements pss
    WHERE pss.mean_exec_time > min_duration_ms
    ORDER BY pss.mean_exec_time DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- СКРИПТ ПРОВЕРКИ ЭФФЕКТИВНОСТИ ИНДЕКСОВ
-- =====================================================

-- Создаем таблицу для логирования производительности
CREATE TABLE IF NOT EXISTS index_performance_log (
    id SERIAL PRIMARY KEY,
    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    table_name TEXT NOT NULL,
    index_name TEXT NOT NULL,
    scans_count BIGINT,
    tuples_read BIGINT,
    tuples_fetched BIGINT,
    index_size BIGINT,
    effectiveness_score NUMERIC
);

-- Функция для регулярной проверки эффективности индексов
CREATE OR REPLACE FUNCTION log_index_performance()
RETURNS void AS $$
DECLARE
    rec RECORD;
BEGIN
    -- Очищаем старые записи (старше 30 дней)
    DELETE FROM index_performance_log 
    WHERE check_date < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    -- Записываем текущую статистику
    FOR rec IN 
        SELECT 
            s.tablename,
            s.indexname,
            s.idx_scan,
            s.idx_tup_read,
            s.idx_tup_fetch,
            pg_relation_size(s.indexrelid) as index_size,
            CASE 
                WHEN s.idx_scan = 0 THEN 0
                ELSE (s.idx_tup_fetch::numeric / s.idx_scan) * 
                     (s.idx_scan::numeric / GREATEST(pg_relation_size(s.indexrelid) / 8192, 1))
            END as effectiveness_score
        FROM pg_stat_user_indexes s
        WHERE s.schemaname = 'public'
    LOOP
        INSERT INTO index_performance_log (
            table_name, index_name, scans_count, tuples_read, 
            tuples_fetched, index_size, effectiveness_score
        ) VALUES (
            rec.tablename, rec.indexname, rec.idx_scan, rec.idx_tup_read,
            rec.idx_tup_fetch, rec.index_size, rec.effectiveness_score
        );
    END LOOP;
    
    RAISE NOTICE 'Статистика индексов обновлена';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- РЕКОМЕНДАЦИИ ПО ОБСЛУЖИВАНИЮ ИНДЕКСОВ
-- =====================================================

/*
РЕКОМЕНДАЦИИ ПО ИСПОЛЬЗОВАНИЮ:

1. Мониторинг эффективности:
   - Запускайте analyze_index_usage() еженедельно
   - Проверяйте find_unused_indexes() ежемесячно
   - Анализируйте analyze_slow_queries() ежедневно

2. Обслуживание индексов:
   - REINDEX CONCURRENTLY для фрагментированных индексов
   - VACUUM ANALYZE после массовых операций
   - Мониторинг размера индексов

3. Настройка PostgreSQL для оптимальной работы индексов:
   - shared_buffers = 25% от RAM
   - effective_cache_size = 75% от RAM
   - random_page_cost = 1.1 (для SSD)
   - work_mem = 256MB (для сложных запросов)

4. Автоматизация:
   - Настройте cron для log_index_performance()
   - Мониторинг через Prometheus/Grafana
   - Алерты на неэффективные индексы

ПРИМЕРЫ ЗАПРОСОВ ДЛЯ МОНИТОРИНГА:

-- Проверка использования индексов
SELECT * FROM analyze_index_usage() WHERE usage_ratio < 0.1;

-- Поиск неиспользуемых индексов
SELECT * FROM find_unused_indexes();

-- Анализ медленных запросов
SELECT * FROM analyze_slow_queries(500);

-- Размеры индексов
SELECT 
    schemaname, tablename, indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes 
ORDER BY pg_relation_size(indexrelid) DESC;
*/

-- =====================================================
-- ЗАВЕРШЕНИЕ МИГРАЦИИ
-- =====================================================

-- Обновляем статистику после создания индексов
ANALYZE database_metrics;
ANALYZE alerts;
ANALYZE recommendations;
ANALYZE database_connections;
ANALYZE query_statistics;
ANALYZE ml_models;
ANALYZE task_results;

-- Логируем создание индексов
DO $$
BEGIN
    RAISE NOTICE 'Миграция 001_add_performance_indexes завершена успешно';
    RAISE NOTICE 'Создано % индексов для оптимизации производительности', 
        (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' 
         AND indexname LIKE 'idx_%');
END $$;

