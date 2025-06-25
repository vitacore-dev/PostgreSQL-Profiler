from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry

class PrometheusMetrics:
    def __init__(self):
        # Создаем собственный реестр для избежания дублирования
        self.registry = CollectorRegistry()
        
        # HTTP метрики
        self.http_requests_total = Counter(
            'postgresql_profiler_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.http_request_duration_seconds = Histogram(
            'postgresql_profiler_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        # Метрики базы данных
        self.database_connections_total = Gauge(
            'postgresql_profiler_database_connections_total',
            'Total number of database connections',
            registry=self.registry
        )
        
        self.active_alerts_total = Gauge(
            'postgresql_profiler_active_alerts_total',
            'Total number of active alerts',
            ['severity'],
            registry=self.registry
        )
        
        self.database_query_duration = Histogram(
            'postgresql_profiler_database_query_duration_seconds',
            'Database query duration in seconds',
            ['database_id', 'query_type'],
            registry=self.registry
        )
        
        # Системные метрики
        self.system_cpu_usage = Gauge(
            'postgresql_profiler_system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'postgresql_profiler_system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )
        
        # Информационные метрики
        self.app_info = Info(
            'postgresql_profiler_app_info',
            'Application information',
            registry=self.registry
        )
        
        # Инициализация информационных метрик
        self.app_info.info({
            'version': '1.0.0',
            'name': 'PostgreSQL Profiler'
        })
