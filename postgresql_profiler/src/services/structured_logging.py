import structlog
from functools import wraps

def init_logging(app):
    pass

def get_logger(name):
    return structlog.get_logger(name)

def log_function_call(func):
    """Декоратор для логирования вызовов функций"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
