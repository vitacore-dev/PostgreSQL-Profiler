import asyncio
import asyncpg
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ConnectionConfig:
    """Конфигурация подключения к PostgreSQL"""
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_mode: str = 'prefer'

class PostgreSQLMonitor:
    """Сервис для мониторинга PostgreSQL"""
    
    def __init__(self):
        self.connections: Dict[int, asyncpg.Connection] = {}
        self.connection_pools: Dict[int, asyncpg.Pool] = {}
    
    async def create_connection_pool(self, db_id: int, config: ConnectionConfig) -> bool:
        """Создает пул соединений для базы данных"""
        try:
            pool = await asyncpg.create_pool(
                host=config.host,
                port=config.port,
                database=config.database,
                user=config.username,
                password=config.password,
                ssl=config.ssl_mode,
                min_size=1,
                max_size=5,
                command_timeout=30
            )
            self.connection_pools[db_id] = pool
            logger.info(f"Created connection pool for database {db_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create connection pool for database {db_id}: {e}")
            return False
    
    async def close_connection_pool(self, db_id: int):
        """Закрывает пул соединений"""
        if db_id in self.connection_pools:
            await self.connection_pools[db_id].close()
            del self.connection_pools[db_id]
            logger.info(f"Closed connection pool for database {db_id}")
    
    async def test_connection(self, config: ConnectionConfig) -> Dict[str, Any]:
        """Тестирует подключение к базе данных"""
        try:
            conn = await asyncpg.connect(
                host=config.host,
                port=config.port,
                database=config.database,
                user=config.username,
                password=config.password,
                ssl=config.ssl_mode
            )
            
            # Получаем базовую информацию о сервере
            version = await conn.fetchval("SELECT version()")
            uptime = await conn.fetchval("SELECT date_trunc('second', now() - pg_postmaster_start_time())")
            
            await conn.close()
            
            return {
                'status': 'success',
                'version': version,
                'uptime': str(uptime),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def collect_performance_metrics(self, db_id: int) -> Optional[Dict[str, Any]]:
        """Собирает метрики производительности"""
        if db_id not in self.connection_pools:
            logger.error(f"No connection pool for database {db_id}")
            return None
        
        try:
            async with self.connection_pools[db_id].acquire() as conn:
                metrics = {}
                
                # Метрики соединений
                connection_stats = await conn.fetchrow("""
                    SELECT 
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections,
                        (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
                    FROM pg_stat_activity
                """)
                
                metrics.update({
                    'active_connections': connection_stats['active_connections'],
                    'idle_connections': connection_stats['idle_connections'],
                    'max_connections': connection_stats['max_connections']
                })
                
                # Метрики производительности базы данных
                db_stats = await conn.fetchrow("""
                    SELECT 
                        xact_commit + xact_rollback as total_transactions,
                        tup_returned + tup_fetched + tup_inserted + tup_updated + tup_deleted as total_tuples,
                        blks_read + blks_hit as total_blocks,
                        CASE WHEN blks_read + blks_hit > 0 
                             THEN round((blks_hit::float / (blks_read + blks_hit)) * 100, 2)
                             ELSE 0 
                        END as cache_hit_ratio
                    FROM pg_stat_database 
                    WHERE datname = current_database()
                """)
                
                metrics.update({
                    'total_transactions': db_stats['total_transactions'],
                    'total_tuples': db_stats['total_tuples'],
                    'cache_hit_ratio': db_stats['cache_hit_ratio']
                })
                
                # Метрики блокировок
                lock_stats = await conn.fetchrow("""
                    SELECT 
                        count(*) as locks_count,
                        count(*) FILTER (WHERE NOT granted) as waiting_locks
                    FROM pg_locks
                """)
                
                metrics.update({
                    'locks_count': lock_stats['locks_count'],
                    'waiting_locks': lock_stats['waiting_locks']
                })
                
                # Метрики размера базы данных
                db_size = await conn.fetchval("SELECT pg_database_size(current_database())")
                metrics['database_size'] = db_size
                
                # Метрики буферного кэша
                buffer_stats = await conn.fetchrow("""
                    SELECT 
                        round(
                            (sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read) + 1)) * 100, 2
                        ) as buffer_cache_hit_ratio
                    FROM pg_statio_user_tables
                """)
                
                if buffer_stats and buffer_stats['buffer_cache_hit_ratio']:
                    metrics['buffer_cache_hit_ratio'] = buffer_stats['buffer_cache_hit_ratio']
                
                metrics['timestamp'] = datetime.utcnow().isoformat()
                return metrics
                
        except Exception as e:
            logger.error(f"Failed to collect metrics for database {db_id}: {e}")
            return None
    
    async def collect_query_statistics(self, db_id: int) -> List[Dict[str, Any]]:
        """Собирает статистику запросов из pg_stat_statements"""
        if db_id not in self.connection_pools:
            logger.error(f"No connection pool for database {db_id}")
            return []
        
        try:
            async with self.connection_pools[db_id].acquire() as conn:
                # Проверяем, установлено ли расширение pg_stat_statements
                extension_exists = await conn.fetchval("""
                    SELECT EXISTS(
                        SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
                    )
                """)
                
                if not extension_exists:
                    logger.warning(f"pg_stat_statements extension not found for database {db_id}")
                    return []
                
                # Получаем статистику запросов
                query_stats = await conn.fetch("""
                    SELECT 
                        query,
                        calls,
                        total_exec_time as total_time,
                        mean_exec_time as mean_time,
                        min_exec_time as min_time,
                        max_exec_time as max_time,
                        rows,
                        shared_blks_hit,
                        shared_blks_read,
                        shared_blks_written,
                        shared_blks_dirtied
                    FROM pg_stat_statements 
                    WHERE query NOT LIKE '%pg_stat_statements%'
                    ORDER BY total_exec_time DESC 
                    LIMIT 100
                """)
                
                results = []
                for row in query_stats:
                    query_hash = hashlib.md5(row['query'].encode()).hexdigest()
                    query_type = self._detect_query_type(row['query'])
                    
                    results.append({
                        'query_hash': query_hash,
                        'query_text': row['query'],
                        'query_type': query_type,
                        'calls': row['calls'],
                        'total_time': row['total_time'],
                        'mean_time': row['mean_time'],
                        'min_time': row['min_time'],
                        'max_time': row['max_time'],
                        'rows_returned': row['rows'],
                        'shared_blks_hit': row['shared_blks_hit'],
                        'shared_blks_read': row['shared_blks_read'],
                        'shared_blks_written': row['shared_blks_written'],
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to collect query statistics for database {db_id}: {e}")
            return []
    
    async def get_active_queries(self, db_id: int) -> List[Dict[str, Any]]:
        """Получает список активных запросов"""
        if db_id not in self.connection_pools:
            return []
        
        try:
            async with self.connection_pools[db_id].acquire() as conn:
                active_queries = await conn.fetch("""
                    SELECT 
                        pid,
                        usename,
                        application_name,
                        client_addr,
                        state,
                        query_start,
                        state_change,
                        query,
                        wait_event_type,
                        wait_event
                    FROM pg_stat_activity 
                    WHERE state = 'active' 
                    AND query NOT LIKE '%pg_stat_activity%'
                    ORDER BY query_start
                """)
                
                results = []
                for row in active_queries:
                    duration = None
                    if row['query_start']:
                        duration = (datetime.utcnow() - row['query_start'].replace(tzinfo=None)).total_seconds()
                    
                    results.append({
                        'pid': row['pid'],
                        'username': row['usename'],
                        'application_name': row['application_name'],
                        'client_addr': str(row['client_addr']) if row['client_addr'] else None,
                        'state': row['state'],
                        'query_start': row['query_start'].isoformat() if row['query_start'] else None,
                        'duration_seconds': duration,
                        'query': row['query'],
                        'wait_event_type': row['wait_event_type'],
                        'wait_event': row['wait_event']
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get active queries for database {db_id}: {e}")
            return []
    
    async def get_table_statistics(self, db_id: int) -> List[Dict[str, Any]]:
        """Получает статистику по таблицам"""
        if db_id not in self.connection_pools:
            return []
        
        try:
            async with self.connection_pools[db_id].acquire() as conn:
                table_stats = await conn.fetch("""
                    SELECT 
                        schemaname,
                        tablename,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del,
                        n_live_tup,
                        n_dead_tup,
                        last_vacuum,
                        last_autovacuum,
                        last_analyze,
                        last_autoanalyze
                    FROM pg_stat_user_tables
                    ORDER BY seq_tup_read + idx_tup_fetch DESC
                    LIMIT 50
                """)
                
                results = []
                for row in table_stats:
                    # Получаем размер таблицы
                    table_size = await conn.fetchval("""
                        SELECT pg_total_relation_size($1::regclass)
                    """, f"{row['schemaname']}.{row['tablename']}")
                    
                    results.append({
                        'schema_name': row['schemaname'],
                        'table_name': row['tablename'],
                        'seq_scan': row['seq_scan'],
                        'seq_tup_read': row['seq_tup_read'],
                        'idx_scan': row['idx_scan'],
                        'idx_tup_fetch': row['idx_tup_fetch'],
                        'n_tup_ins': row['n_tup_ins'],
                        'n_tup_upd': row['n_tup_upd'],
                        'n_tup_del': row['n_tup_del'],
                        'n_live_tup': row['n_live_tup'],
                        'n_dead_tup': row['n_dead_tup'],
                        'table_size': table_size,
                        'last_vacuum': row['last_vacuum'].isoformat() if row['last_vacuum'] else None,
                        'last_autovacuum': row['last_autovacuum'].isoformat() if row['last_autovacuum'] else None,
                        'last_analyze': row['last_analyze'].isoformat() if row['last_analyze'] else None,
                        'last_autoanalyze': row['last_autoanalyze'].isoformat() if row['last_autoanalyze'] else None
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get table statistics for database {db_id}: {e}")
            return []
    
    def _detect_query_type(self, query: str) -> str:
        """Определяет тип SQL запроса"""
        query_upper = query.strip().upper()
        
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        elif query_upper.startswith('CREATE'):
            return 'CREATE'
        elif query_upper.startswith('ALTER'):
            return 'ALTER'
        elif query_upper.startswith('DROP'):
            return 'DROP'
        else:
            return 'OTHER'

# Глобальный экземпляр монитора
postgresql_monitor = PostgreSQLMonitor()

