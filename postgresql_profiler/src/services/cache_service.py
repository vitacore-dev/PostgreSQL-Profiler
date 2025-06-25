from functools import wraps
import json
import hashlib
from flask import request

class CacheService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_timeout = 300  # 5 минут
    
    def get(self, key):
        """Получить значение из кэша"""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value.decode('utf-8'))
        except Exception as e:
            print(f"Cache get error: {e}")
        return None
    
    def set(self, key, value, timeout=None):
        """Сохранить значение в кэш"""
        try:
            timeout = timeout or self.default_timeout
            serialized = json.dumps(value, default=str)
            self.redis.setex(key, timeout, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key):
        """Удалить значение из кэша"""
        try:
            return self.redis.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern):
        """Удалить все ключи по паттерну"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
        return 0

def cache_response(timeout=300):
    """Декоратор для кэширования ответов API"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Создаем ключ кэша на основе URL и параметров
                cache_key = _generate_cache_key(func.__name__, request)
                
                # Проверяем наличие в кэше
                from flask import current_app
                cached_result = current_app.cache_service.get(cache_key)
                if cached_result:
                    return cached_result
                
                # Выполняем функцию и кэшируем результат
                result = func(*args, **kwargs)
                current_app.cache_service.set(cache_key, result, timeout)
                return result
            except Exception as e:
                print(f"Cache decorator error: {e}")
                # В случае ошибки кэширования, выполняем функцию без кэша
                return func(*args, **kwargs)
        return wrapper
    return decorator

def _generate_cache_key(func_name, request):
    """Генерирует ключ кэша на основе имени функции и параметров запроса"""
    key_data = f"{func_name}:{request.url}:{request.method}"
    if request.args:
        key_data += f":{sorted(request.args.items())}"
    return hashlib.md5(key_data.encode()).hexdigest()
