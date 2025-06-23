-- Инициализация базы данных для PostgreSQL Profiler
-- Автор: Manus AI
-- Дата: 18 июня 2025

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Создание схемы для профилировщика
CREATE SCHEMA IF NOT EXISTS profiler;

-- Таблица подключений к базам данных
CREATE TABLE IF NOT EXISTS profiler.database_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL DEFAULT 5432,
    database_name VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    password_encrypted TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_connected_at TIMESTAMP,
    connection_params JSONB DEFAULT '{}'::jsonb
);

-- Таблица метрик производительности
CREATE TABLE IF NOT EXISTS profiler.performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID REFERENCES profiler.database_connections(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value NUMERIC NOT NULL,
    metric_unit VARCHAR(50),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Таблица алертов
CREATE TABLE IF NOT EXISTS profiler.alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID REFERENCES profiler.database_connections(id) ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Таблица рекомендаций
CREATE TABLE IF NOT EXISTS profiler.recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID REFERENCES profiler.database_connections(id) ON DELETE CASCADE,
    recommendation_type VARCHAR(100) NOT NULL,
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('low', 'medium', 'high')),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    sql_suggestion TEXT,
    impact_estimate VARCHAR(100),
    is_applied BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Таблица медленных запросов
CREATE TABLE IF NOT EXISTS profiler.slow_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID REFERENCES profiler.database_connections(id) ON DELETE CASCADE,
    query_hash VARCHAR(64) NOT NULL,
    query_text TEXT NOT NULL,
    execution_time NUMERIC NOT NULL,
    calls_count INTEGER DEFAULT 1,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    avg_execution_time NUMERIC,
    max_execution_time NUMERIC,
    min_execution_time NUMERIC,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Таблица статистики индексов
CREATE TABLE IF NOT EXISTS profiler.index_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID REFERENCES profiler.database_connections(id) ON DELETE CASCADE,
    schema_name VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    index_name VARCHAR(255) NOT NULL,
    index_size BIGINT,
    scans_count BIGINT DEFAULT 0,
    tuples_read BIGINT DEFAULT 0,
    tuples_fetched BIGINT DEFAULT 0,
    is_unique BOOLEAN DEFAULT false,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_performance_metrics_connection_time 
ON profiler.performance_metrics(connection_id, collected_at);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_type_time 
ON profiler.performance_metrics(metric_type, collected_at);

CREATE INDEX IF NOT EXISTS idx_alerts_connection_active 
ON profiler.alerts(connection_id, is_active);

CREATE INDEX IF NOT EXISTS idx_alerts_severity_created 
ON profiler.alerts(severity, created_at);

CREATE INDEX IF NOT EXISTS idx_recommendations_connection_priority 
ON profiler.recommendations(connection_id, priority);

CREATE INDEX IF NOT EXISTS idx_slow_queries_connection_time 
ON profiler.slow_queries(connection_id, last_seen);

CREATE INDEX IF NOT EXISTS idx_slow_queries_execution_time 
ON profiler.slow_queries(execution_time DESC);

CREATE INDEX IF NOT EXISTS idx_index_statistics_connection_collected 
ON profiler.index_statistics(connection_id, collected_at);

-- Функция для очистки старых данных
CREATE OR REPLACE FUNCTION profiler.cleanup_old_data(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER := 0;
    temp_count INTEGER;
BEGIN
    -- Очистка старых метрик
    DELETE FROM profiler.performance_metrics 
    WHERE collected_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    -- Очистка решенных алертов старше 30 дней
    DELETE FROM profiler.alerts 
    WHERE resolved_at IS NOT NULL 
    AND resolved_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    -- Очистка старых записей медленных запросов
    DELETE FROM profiler.slow_queries 
    WHERE last_seen < CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    -- Очистка старой статистики индексов
    DELETE FROM profiler.index_statistics 
    WHERE collected_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    RETURN deleted_count;
END;
$$;

-- Функция для получения статистики системы
CREATE OR REPLACE FUNCTION profiler.get_system_stats()
RETURNS TABLE(
    total_connections INTEGER,
    active_connections INTEGER,
    total_metrics BIGINT,
    active_alerts INTEGER,
    pending_recommendations INTEGER,
    slow_queries_count BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*)::INTEGER FROM profiler.database_connections),
        (SELECT COUNT(*)::INTEGER FROM profiler.database_connections WHERE is_active = true),
        (SELECT COUNT(*) FROM profiler.performance_metrics),
        (SELECT COUNT(*)::INTEGER FROM profiler.alerts WHERE is_active = true),
        (SELECT COUNT(*)::INTEGER FROM profiler.recommendations WHERE is_applied = false),
        (SELECT COUNT(*) FROM profiler.slow_queries);
END;
$$;

-- Создание пользователя для приложения (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'profiler_app') THEN
        CREATE ROLE profiler_app WITH LOGIN PASSWORD 'profiler_app_password';
    END IF;
END
$$;

-- Предоставление прав пользователю приложения
GRANT USAGE ON SCHEMA profiler TO profiler_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA profiler TO profiler_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA profiler TO profiler_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA profiler TO profiler_app;

-- Настройка автоматической очистки данных (запуск каждый день в 2:00)
-- Примечание: требует расширения pg_cron для автоматического выполнения
-- SELECT cron.schedule('cleanup-profiler-data', '0 2 * * *', 'SELECT profiler.cleanup_old_data(90);');

-- Вставка тестовых данных для демонстрации
INSERT INTO profiler.database_connections (name, host, port, database_name, username, password_encrypted)
VALUES 
    ('Local PostgreSQL', 'localhost', 5432, 'postgres', 'postgres', 'encrypted_password_here'),
    ('Production DB', 'prod-db.example.com', 5432, 'production', 'app_user', 'encrypted_password_here')
ON CONFLICT DO NOTHING;

-- Создание представлений для удобства
CREATE OR REPLACE VIEW profiler.v_active_connections AS
SELECT 
    id,
    name,
    host,
    port,
    database_name,
    username,
    created_at,
    last_connected_at,
    CASE 
        WHEN last_connected_at > CURRENT_TIMESTAMP - INTERVAL '5 minutes' THEN 'online'
        WHEN last_connected_at > CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN 'recent'
        ELSE 'offline'
    END as status
FROM profiler.database_connections
WHERE is_active = true;

CREATE OR REPLACE VIEW profiler.v_recent_metrics AS
SELECT 
    pm.id,
    dc.name as connection_name,
    pm.metric_type,
    pm.metric_name,
    pm.metric_value,
    pm.metric_unit,
    pm.collected_at
FROM profiler.performance_metrics pm
JOIN profiler.database_connections dc ON pm.connection_id = dc.id
WHERE pm.collected_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY pm.collected_at DESC;

CREATE OR REPLACE VIEW profiler.v_critical_alerts AS
SELECT 
    a.id,
    dc.name as connection_name,
    a.alert_type,
    a.severity,
    a.title,
    a.description,
    a.created_at
FROM profiler.alerts a
JOIN profiler.database_connections dc ON a.connection_id = dc.id
WHERE a.is_active = true AND a.severity IN ('high', 'critical')
ORDER BY a.created_at DESC;

-- Логирование завершения инициализации
INSERT INTO profiler.performance_metrics (connection_id, metric_type, metric_name, metric_value, metric_unit)
SELECT 
    id, 
    'system', 
    'database_initialized', 
    1, 
    'boolean'
FROM profiler.database_connections 
LIMIT 1;

-- Вывод информации о завершении
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL Profiler database initialization completed successfully!';
    RAISE NOTICE 'Schema: profiler';
    RAISE NOTICE 'Tables created: %, %, %, %, %, %', 
        'database_connections', 'performance_metrics', 'alerts', 
        'recommendations', 'slow_queries', 'index_statistics';
END
$$;

