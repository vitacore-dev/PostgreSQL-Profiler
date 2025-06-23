from functools import wraps

class CacheService:
    def __init__(self, redis_client):
        self.redis = redis_client

def cache_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
