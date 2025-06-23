# Оптимизированные ML-задачи для Celery
import os
import joblib
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from celery import shared_task
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import structlog

from ..models.profiler import DatabaseMetric, DatabaseConnection, Alert, Recommendation
from ..main import db

# Настройка логирования
logger = structlog.get_logger(__name__)

# Константы для ML моделей
MODEL_DIR = "ml_models"
MIN_TRAIN_SIZE = 50
MIN_PREDICTION_SIZE = 10
MODEL_RETRAIN_THRESHOLD = 0.8  # R2 score threshold for retraining

# Пути к моделям
LOAD_PREDICTOR_PATH = os.path.join(MODEL_DIR, "load_predictor.pkl")
ANOMALY_DETECTOR_PATH = os.path.join(MODEL_DIR, "anomaly_detector.pkl")
QUERY_TIME_PREDICTOR_PATH = os.path.join(MODEL_DIR, "query_time_predictor.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")

# Создание директории для моделей
os.makedirs(MODEL_DIR, exist_ok=True)

@shared_task(bind=True, max_retries=3)
def train_load_predictor(self, database_id: Optional[int] = None):
    """
    Обучение модели прогнозирования нагрузки
    """
    try:
        logger.info("Начало обучения модели прогнозирования нагрузки", database_id=database_id)
        
        # Получение исторических метрик
        query = DatabaseMetric.query.order_by(DatabaseMetric.timestamp.desc())
        if database_id:
            query = query.filter(DatabaseMetric.database_id == database_id)
        
        historical_metrics = query.limit(10000).all()  # Ограничиваем количество для производительности
        
        if len(historical_metrics) < MIN_TRAIN_SIZE:
            logger.warning(
                "Недостаточно данных для обучения модели прогнозирования нагрузки",
                available_records=len(historical_metrics),
                required_records=MIN_TRAIN_SIZE,
                database_id=database_id
            )
            return {
                "status": "insufficient_data",
                "records": len(historical_metrics),
                "required": MIN_TRAIN_SIZE
            }
        
        # Подготовка данных
        features = []
        targets = []
        
        for metric in historical_metrics:
            if all(v is not None for v in [
                metric.cpu_usage, metric.memory_usage, 
                metric.disk_io, metric.active_connections,
                metric.cache_hit_ratio, metric.avg_query_time
            ]):
                features.append([
                    metric.cpu_usage,
                    metric.memory_usage,
                    metric.disk_io,
                    metric.active_connections,
                    metric.cache_hit_ratio,
                    metric.avg_query_time,
                    metric.locks_count or 0,
                    metric.deadlocks_count or 0
                ])
                
                # Вычисляем общую нагрузку как взвешенную сумму метрик
                load = (
                    metric.cpu_usage * 0.3 +
                    metric.memory_usage * 0.3 +
                    (metric.disk_io / 1000) * 0.2 +  # Нормализуем disk_io
                    (metric.active_connections / 100) * 0.1 +
                    (100 - metric.cache_hit_ratio) * 0.1  # Инвертируем cache hit ratio
                )
                targets.append(load)
        
        if len(features) < MIN_TRAIN_SIZE:
            logger.warning(
                "Недостаточно валидных данных после фильтрации",
                valid_records=len(features),
                total_records=len(historical_metrics)
            )
            return {
                "status": "insufficient_valid_data",
                "valid_records": len(features),
                "total_records": len(historical_metrics)
            }
        
        X = np.array(features)
        y = np.array(targets)
        
        # Нормализация данных
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Разделение на обучающую и тестовую выборки
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Обучение модели
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        # Оценка качества модели
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        logger.info(
            "Модель прогнозирования нагрузки обучена",
            mse=mse,
            r2_score=r2,
            training_samples=len(X_train),
            test_samples=len(X_test)
        )
        
        # Сохранение модели и скейлера
        model_path = LOAD_PREDICTOR_PATH
        if database_id:
            model_path = f"{MODEL_DIR}/load_predictor_db_{database_id}.pkl"
            
        scaler_path = SCALER_PATH
        if database_id:
            scaler_path = f"{MODEL_DIR}/scaler_db_{database_id}.pkl"
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        logger.info(
            "Модель и скейлер сохранены",
            model_path=model_path,
            scaler_path=scaler_path
        )
        
        return {
            "status": "success",
            "model_path": model_path,
            "mse": mse,
            "r2_score": r2,
            "training_samples": len(X_train),
            "feature_importance": model.feature_importances_.tolist()
        }
        
    except Exception as exc:
        logger.error("Ошибка при обучении модели прогнозирования нагрузки", error=str(exc))
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3)
def train_anomaly_detector(self, database_id: Optional[int] = None):
    """
    Обучение модели детекции аномалий
    """
    try:
        logger.info("Начало обучения модели детекции аномалий", database_id=database_id)
        
        # Получение исторических метрик
        query = DatabaseMetric.query.order_by(DatabaseMetric.timestamp.desc())
        if database_id:
            query = query.filter(DatabaseMetric.database_id == database_id)
        
        historical_metrics = query.limit(5000).all()
        
        if len(historical_metrics) < MIN_TRAIN_SIZE:
            logger.warning(
                "Недостаточно данных для обучения модели детекции аномалий",
                available_records=len(historical_metrics),
                required_records=MIN_TRAIN_SIZE
            )
            return {"status": "insufficient_data"}
        
        # Подготовка данных
        features = []
        for metric in historical_metrics:
            if all(v is not None for v in [
                metric.cpu_usage, metric.memory_usage,
                metric.active_connections, metric.avg_query_time
            ]):
                features.append([
                    metric.cpu_usage,
                    metric.memory_usage,
                    metric.active_connections,
                    metric.avg_query_time,
                    metric.cache_hit_ratio or 95.0,
                    metric.locks_count or 0,
                    metric.deadlocks_count or 0
                ])
        
        if len(features) < MIN_TRAIN_SIZE:
            logger.warning("Недостаточно валидных данных для детекции аномалий")
            return {"status": "insufficient_valid_data"}
        
        X = np.array(features)
        
        # Нормализация данных
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Обучение модели детекции аномалий
        model = IsolationForest(
            contamination=0.1,  # Ожидаем 10% аномалий
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_scaled)
        
        # Сохранение модели
        model_path = ANOMALY_DETECTOR_PATH
        scaler_path = f"{MODEL_DIR}/anomaly_scaler.pkl"
        
        if database_id:
            model_path = f"{MODEL_DIR}/anomaly_detector_db_{database_id}.pkl"
            scaler_path = f"{MODEL_DIR}/anomaly_scaler_db_{database_id}.pkl"
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        logger.info(
            "Модель детекции аномалий обучена и сохранена",
            model_path=model_path,
            training_samples=len(X)
        )
        
        return {
            "status": "success",
            "model_path": model_path,
            "training_samples": len(X)
        }
        
    except Exception as exc:
        logger.error("Ошибка при обучении модели детекции аномалий", error=str(exc))
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3)
def train_query_time_predictor(self, database_id: Optional[int] = None):
    """
    Обучение модели прогнозирования времени выполнения запросов
    """
    try:
        logger.info("Начало обучения модели прогнозирования времени запросов", database_id=database_id)
        
        # Получение исторических метрик
        query = DatabaseMetric.query.order_by(DatabaseMetric.timestamp.desc())
        if database_id:
            query = query.filter(DatabaseMetric.database_id == database_id)
        
        historical_metrics = query.limit(5000).all()
        
        if len(historical_metrics) < MIN_TRAIN_SIZE:
            logger.warning(
                "Недостаточно данных для обучения модели прогнозирования времени запросов",
                available_records=len(historical_metrics)
            )
            return {"status": "insufficient_data"}
        
        # Подготовка данных
        features = []
        targets = []
        
        for metric in historical_metrics:
            if all(v is not None for v in [
                metric.cpu_usage, metric.memory_usage,
                metric.active_connections, metric.avg_query_time
            ]) and metric.avg_query_time > 0:
                features.append([
                    metric.cpu_usage,
                    metric.memory_usage,
                    metric.active_connections,
                    metric.cache_hit_ratio or 95.0,
                    metric.locks_count or 0
                ])
                targets.append(metric.avg_query_time)
        
        if len(features) < MIN_TRAIN_SIZE:
            return {"status": "insufficient_valid_data"}
        
        X = np.array(features)
        y = np.array(targets)
        
        # Нормализация данных
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Разделение данных
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Обучение модели
        model = RandomForestRegressor(
            n_estimators=50,
            max_depth=8,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        # Оценка качества
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Сохранение модели
        model_path = QUERY_TIME_PREDICTOR_PATH
        scaler_path = f"{MODEL_DIR}/query_time_scaler.pkl"
        
        if database_id:
            model_path = f"{MODEL_DIR}/query_time_predictor_db_{database_id}.pkl"
            scaler_path = f"{MODEL_DIR}/query_time_scaler_db_{database_id}.pkl"
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        logger.info(
            "Модель прогнозирования времени запросов обучена",
            model_path=model_path,
            mse=mse,
            r2_score=r2
        )
        
        return {
            "status": "success",
            "model_path": model_path,
            "mse": mse,
            "r2_score": r2,
            "training_samples": len(X_train)
        }
        
    except Exception as exc:
        logger.error("Ошибка при обучении модели прогнозирования времени запросов", error=str(exc))
        raise self.retry(exc=exc, countdown=60)

@shared_task
def train_all_models():
    """
    Обучение всех ML моделей для всех активных баз данных
    """
    try:
        logger.info("Начало обучения всех ML моделей")
        
        # Получение всех активных баз данных
        active_databases = DatabaseConnection.query.filter_by(is_active=True).all()
        
        results = {
            "global_models": {},
            "database_models": {}
        }
        
        # Обучение глобальных моделей (на данных всех БД)
        logger.info("Обучение глобальных моделей")
        results["global_models"]["load_predictor"] = train_load_predictor.delay().get()
        results["global_models"]["anomaly_detector"] = train_anomaly_detector.delay().get()
        results["global_models"]["query_time_predictor"] = train_query_time_predictor.delay().get()
        
        # Обучение моделей для каждой БД отдельно
        for db_conn in active_databases:
            logger.info("Обучение моделей для базы данных", database_id=db_conn.id, database_name=db_conn.name)
            
            db_results = {}
            db_results["load_predictor"] = train_load_predictor.delay(db_conn.id).get()
            db_results["anomaly_detector"] = train_anomaly_detector.delay(db_conn.id).get()
            db_results["query_time_predictor"] = train_query_time_predictor.delay(db_conn.id).get()
            
            results["database_models"][db_conn.id] = db_results
        
        logger.info("Обучение всех моделей завершено", results=results)
        return results
        
    except Exception as exc:
        logger.error("Ошибка при обучении всех моделей", error=str(exc))
        raise

@shared_task
def cleanup_old_models():
    """
    Очистка старых файлов моделей
    """
    try:
        logger.info("Начало очистки старых моделей")
        
        if not os.path.exists(MODEL_DIR):
            return {"status": "no_models_directory"}
        
        # Получение всех файлов моделей
        model_files = []
        for file in os.listdir(MODEL_DIR):
            if file.endswith('.pkl'):
                file_path = os.path.join(MODEL_DIR, file)
                file_stat = os.stat(file_path)
                model_files.append({
                    "path": file_path,
                    "name": file,
                    "modified": datetime.fromtimestamp(file_stat.st_mtime)
                })
        
        # Удаление файлов старше 7 дней
        cutoff_date = datetime.now() - timedelta(days=7)
        deleted_files = []
        
        for model_file in model_files:
            if model_file["modified"] < cutoff_date:
                os.remove(model_file["path"])
                deleted_files.append(model_file["name"])
                logger.info("Удален старый файл модели", file=model_file["name"])
        
        logger.info("Очистка моделей завершена", deleted_count=len(deleted_files))
        return {
            "status": "success",
            "deleted_files": deleted_files,
            "deleted_count": len(deleted_files)
        }
        
    except Exception as exc:
        logger.error("Ошибка при очистке моделей", error=str(exc))
        raise

def load_model(model_path: str) -> Optional[Any]:
    """
    Загрузка модели с диска
    """
    try:
        if not os.path.exists(model_path):
            logger.warning("Файл модели не найден", model_path=model_path)
            return None
        
        model = joblib.load(model_path)
        logger.debug("Модель загружена успешно", model_path=model_path)
        return model
        
    except Exception as exc:
        logger.error("Ошибка при загрузке модели", model_path=model_path, error=str(exc))
        return None

def get_model_paths(database_id: Optional[int] = None) -> Dict[str, str]:
    """
    Получение путей к моделям для конкретной БД или глобальным
    """
    if database_id:
        return {
            "load_predictor": f"{MODEL_DIR}/load_predictor_db_{database_id}.pkl",
            "load_scaler": f"{MODEL_DIR}/scaler_db_{database_id}.pkl",
            "anomaly_detector": f"{MODEL_DIR}/anomaly_detector_db_{database_id}.pkl",
            "anomaly_scaler": f"{MODEL_DIR}/anomaly_scaler_db_{database_id}.pkl",
            "query_time_predictor": f"{MODEL_DIR}/query_time_predictor_db_{database_id}.pkl",
            "query_time_scaler": f"{MODEL_DIR}/query_time_scaler_db_{database_id}.pkl"
        }
    else:
        return {
            "load_predictor": LOAD_PREDICTOR_PATH,
            "load_scaler": SCALER_PATH,
            "anomaly_detector": ANOMALY_DETECTOR_PATH,
            "anomaly_scaler": f"{MODEL_DIR}/anomaly_scaler.pkl",
            "query_time_predictor": QUERY_TIME_PREDICTOR_PATH,
            "query_time_scaler": f"{MODEL_DIR}/query_time_scaler.pkl"
        }

