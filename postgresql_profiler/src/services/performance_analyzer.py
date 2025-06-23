# Обновлённый анализатор производительности с оптимизированными ML-моделями
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import structlog

from .ml_tasks import load_model, get_model_paths, MIN_TRAIN_SIZE, MIN_PREDICTION_SIZE
from ..models.profiler import DatabaseMetric, DatabaseConnection, Alert, Recommendation
from ..main import db

logger = structlog.get_logger(__name__)

class OptimizedPerformanceAnalyzer:
    """
    Оптимизированный анализатор производительности с использованием предобученных ML-моделей
    """
    
    def __init__(self):
        self.models_cache = {}
        self.scalers_cache = {}
        self.cache_ttl = 3600  # 1 час кэширования моделей в памяти
        self.last_cache_update = {}
    
    def _get_cached_model(self, model_key: str, model_path: str) -> Optional[Any]:
        """
        Получение модели из кэша или загрузка с диска
        """
        current_time = datetime.now()
        
        # Проверяем, нужно ли обновить кэш
        if (model_key in self.last_cache_update and 
            (current_time - self.last_cache_update[model_key]).seconds < self.cache_ttl and
            model_key in self.models_cache):
            return self.models_cache[model_key]
        
        # Загружаем модель с диска
        model = load_model(model_path)
        if model is not None:
            self.models_cache[model_key] = model
            self.last_cache_update[model_key] = current_time
            logger.debug("Модель загружена в кэш", model_key=model_key)
        
        return model
    
    def predict_load(self, latest_metrics: DatabaseMetric, database_id: Optional[int] = None) -> Optional[float]:
        """
        Прогнозирование нагрузки с использованием предобученной модели
        """
        try:
            # Получаем пути к моделям
            model_paths = get_model_paths(database_id)
            
            # Пытаемся загрузить специфичную для БД модель, если не получается - глобальную
            model_key = f"load_predictor_{database_id}" if database_id else "load_predictor_global"
            scaler_key = f"load_scaler_{database_id}" if database_id else "load_scaler_global"
            
            model = self._get_cached_model(model_key, model_paths["load_predictor"])
            scaler = self._get_cached_model(scaler_key, model_paths["load_scaler"])
            
            # Если специфичная модель не найдена, используем глобальную
            if model is None and database_id:
                global_paths = get_model_paths(None)
                model = self._get_cached_model("load_predictor_global", global_paths["load_predictor"])
                scaler = self._get_cached_model("load_scaler_global", global_paths["load_scaler"])
            
            if model is None or scaler is None:
                logger.warning(
                    "Модель прогнозирования нагрузки не найдена",
                    database_id=database_id,
                    model_found=model is not None,
                    scaler_found=scaler is not None
                )
                return None
            
            # Проверяем достаточность исторических данных
            historical_count = self._get_historical_metrics_count(database_id)
            if historical_count < MIN_PREDICTION_SIZE:
                logger.warning(
                    "Недостаточно исторических данных для прогнозирования",
                    available_records=historical_count,
                    required_records=MIN_PREDICTION_SIZE,
                    database_id=database_id
                )
                return None
            
            # Подготавливаем данные для предсказания
            features = self._prepare_load_features(latest_metrics)
            if features is None:
                return None
            
            # Нормализуем данные
            X_pred = scaler.transform([features])
            
            # Делаем предсказание
            prediction = model.predict(X_pred)[0]
            
            logger.info(
                "Прогноз нагрузки выполнен",
                database_id=database_id,
                predicted_load=prediction,
                current_cpu=latest_metrics.cpu_usage,
                current_memory=latest_metrics.memory_usage
            )
            
            return float(prediction)
            
        except Exception as exc:
            logger.error(
                "Ошибка при прогнозировании нагрузки",
                database_id=database_id,
                error=str(exc)
            )
            return None
    
    def detect_anomalies(self, latest_metrics: DatabaseMetric, database_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Детекция аномалий с использованием предобученной модели
        """
        try:
            model_paths = get_model_paths(database_id)
            
            model_key = f"anomaly_detector_{database_id}" if database_id else "anomaly_detector_global"
            scaler_key = f"anomaly_scaler_{database_id}" if database_id else "anomaly_scaler_global"
            
            model = self._get_cached_model(model_key, model_paths["anomaly_detector"])
            scaler = self._get_cached_model(scaler_key, model_paths["anomaly_scaler"])
            
            # Fallback к глобальной модели
            if model is None and database_id:
                global_paths = get_model_paths(None)
                model = self._get_cached_model("anomaly_detector_global", global_paths["anomaly_detector"])
                scaler = self._get_cached_model("anomaly_scaler_global", global_paths["anomaly_scaler"])
            
            if model is None or scaler is None:
                logger.warning("Модель детекции аномалий не найдена", database_id=database_id)
                return {"anomaly_detected": False, "reason": "model_not_found"}
            
            # Подготавливаем данные
            features = self._prepare_anomaly_features(latest_metrics)
            if features is None:
                return {"anomaly_detected": False, "reason": "invalid_features"}
            
            # Нормализуем и предсказываем
            X_pred = scaler.transform([features])
            anomaly_score = model.decision_function(X_pred)[0]
            is_anomaly = model.predict(X_pred)[0] == -1
            
            result = {
                "anomaly_detected": bool(is_anomaly),
                "anomaly_score": float(anomaly_score),
                "threshold": 0.0,
                "features_analyzed": len(features)
            }
            
            if is_anomaly:
                logger.warning(
                    "Обнаружена аномалия в производительности",
                    database_id=database_id,
                    anomaly_score=anomaly_score,
                    cpu_usage=latest_metrics.cpu_usage,
                    memory_usage=latest_metrics.memory_usage
                )
                
                # Создаем алерт об аномалии
                self._create_anomaly_alert(latest_metrics, database_id, anomaly_score)
            
            return result
            
        except Exception as exc:
            logger.error("Ошибка при детекции аномалий", database_id=database_id, error=str(exc))
            return {"anomaly_detected": False, "reason": "error", "error": str(exc)}
    
    def predict_query_time(self, latest_metrics: DatabaseMetric, database_id: Optional[int] = None) -> Optional[float]:
        """
        Прогнозирование времени выполнения запросов
        """
        try:
            model_paths = get_model_paths(database_id)
            
            model_key = f"query_time_predictor_{database_id}" if database_id else "query_time_predictor_global"
            scaler_key = f"query_time_scaler_{database_id}" if database_id else "query_time_scaler_global"
            
            model = self._get_cached_model(model_key, model_paths["query_time_predictor"])
            scaler = self._get_cached_model(scaler_key, model_paths["query_time_scaler"])
            
            # Fallback к глобальной модели
            if model is None and database_id:
                global_paths = get_model_paths(None)
                model = self._get_cached_model("query_time_predictor_global", global_paths["query_time_predictor"])
                scaler = self._get_cached_model("query_time_scaler_global", global_paths["query_time_scaler"])
            
            if model is None or scaler is None:
                logger.warning("Модель прогнозирования времени запросов не найдена", database_id=database_id)
                return None
            
            # Подготавливаем данные
            features = self._prepare_query_time_features(latest_metrics)
            if features is None:
                return None
            
            # Нормализуем и предсказываем
            X_pred = scaler.transform([features])
            prediction = model.predict(X_pred)[0]
            
            logger.debug(
                "Прогноз времени выполнения запросов",
                database_id=database_id,
                predicted_time=prediction,
                current_avg_time=latest_metrics.avg_query_time
            )
            
            return float(prediction)
            
        except Exception as exc:
            logger.error("Ошибка при прогнозировании времени запросов", database_id=database_id, error=str(exc))
            return None
    
    def generate_ml_recommendations(self, database_id: int) -> List[Dict[str, Any]]:
        """
        Генерация рекомендаций на основе ML-анализа
        """
        try:
            recommendations = []
            
            # Получаем последние метрики
            latest_metrics = DatabaseMetric.query.filter_by(database_id=database_id)\
                .order_by(DatabaseMetric.timestamp.desc()).first()
            
            if not latest_metrics:
                return recommendations
            
            # Прогноз нагрузки
            predicted_load = self.predict_load(latest_metrics, database_id)
            if predicted_load and predicted_load > 80:
                recommendations.append({
                    "type": "performance",
                    "priority": "high",
                    "title": "Высокая прогнозируемая нагрузка",
                    "description": f"ML-модель прогнозирует нагрузку {predicted_load:.1f}%. Рекомендуется масштабирование.",
                    "category": "capacity_planning",
                    "impact": "high",
                    "effort": "medium"
                })
            
            # Детекция аномалий
            anomaly_result = self.detect_anomalies(latest_metrics, database_id)
            if anomaly_result.get("anomaly_detected"):
                recommendations.append({
                    "type": "anomaly",
                    "priority": "critical",
                    "title": "Обнаружена аномалия в производительности",
                    "description": f"Аномальное поведение системы (score: {anomaly_result.get('anomaly_score', 0):.3f})",
                    "category": "performance_issue",
                    "impact": "high",
                    "effort": "low"
                })
            
            # Прогноз времени запросов
            predicted_query_time = self.predict_query_time(latest_metrics, database_id)
            if predicted_query_time and predicted_query_time > latest_metrics.avg_query_time * 1.5:
                recommendations.append({
                    "type": "performance",
                    "priority": "medium",
                    "title": "Ожидается увеличение времени выполнения запросов",
                    "description": f"Прогнозируемое время: {predicted_query_time:.1f}ms (текущее: {latest_metrics.avg_query_time:.1f}ms)",
                    "category": "query_optimization",
                    "impact": "medium",
                    "effort": "medium"
                })
            
            # Анализ трендов
            trend_recommendations = self._analyze_performance_trends(database_id)
            recommendations.extend(trend_recommendations)
            
            logger.info(
                "Сгенерированы ML-рекомендации",
                database_id=database_id,
                recommendations_count=len(recommendations)
            )
            
            return recommendations
            
        except Exception as exc:
            logger.error("Ошибка при генерации ML-рекомендаций", database_id=database_id, error=str(exc))
            return []
    
    def _prepare_load_features(self, metrics: DatabaseMetric) -> Optional[List[float]]:
        """
        Подготовка признаков для прогнозирования нагрузки
        """
        try:
            if any(v is None for v in [
                metrics.cpu_usage, metrics.memory_usage,
                metrics.disk_io, metrics.active_connections
            ]):
                return None
            
            return [
                float(metrics.cpu_usage),
                float(metrics.memory_usage),
                float(metrics.disk_io),
                float(metrics.active_connections),
                float(metrics.cache_hit_ratio or 95.0),
                float(metrics.avg_query_time or 0),
                float(metrics.locks_count or 0),
                float(metrics.deadlocks_count or 0)
            ]
        except (ValueError, TypeError):
            return None
    
    def _prepare_anomaly_features(self, metrics: DatabaseMetric) -> Optional[List[float]]:
        """
        Подготовка признаков для детекции аномалий
        """
        try:
            if any(v is None for v in [
                metrics.cpu_usage, metrics.memory_usage,
                metrics.active_connections, metrics.avg_query_time
            ]):
                return None
            
            return [
                float(metrics.cpu_usage),
                float(metrics.memory_usage),
                float(metrics.active_connections),
                float(metrics.avg_query_time),
                float(metrics.cache_hit_ratio or 95.0),
                float(metrics.locks_count or 0),
                float(metrics.deadlocks_count or 0)
            ]
        except (ValueError, TypeError):
            return None
    
    def _prepare_query_time_features(self, metrics: DatabaseMetric) -> Optional[List[float]]:
        """
        Подготовка признаков для прогнозирования времени запросов
        """
        try:
            if any(v is None for v in [
                metrics.cpu_usage, metrics.memory_usage,
                metrics.active_connections
            ]):
                return None
            
            return [
                float(metrics.cpu_usage),
                float(metrics.memory_usage),
                float(metrics.active_connections),
                float(metrics.cache_hit_ratio or 95.0),
                float(metrics.locks_count or 0)
            ]
        except (ValueError, TypeError):
            return None
    
    def _get_historical_metrics_count(self, database_id: Optional[int] = None) -> int:
        """
        Получение количества исторических метрик
        """
        try:
            query = DatabaseMetric.query
            if database_id:
                query = query.filter_by(database_id=database_id)
            return query.count()
        except Exception:
            return 0
    
    def _create_anomaly_alert(self, metrics: DatabaseMetric, database_id: Optional[int], anomaly_score: float):
        """
        Создание алерта об аномалии
        """
        try:
            alert = Alert(
                database_id=database_id,
                alert_type="anomaly",
                severity="high" if anomaly_score < -0.5 else "medium",
                title="Обнаружена аномалия в производительности",
                description=f"ML-модель обнаружила аномальное поведение системы. Аномальный score: {anomaly_score:.3f}",
                alert_source="ml_model",
                metric_name="performance_anomaly",
                metric_value=anomaly_score,
                threshold_value=-0.1,
                alert_metadata={
                    "cpu_usage": metrics.cpu_usage,
                    "memory_usage": metrics.memory_usage,
                    "active_connections": metrics.active_connections,
                    "avg_query_time": metrics.avg_query_time,
                    "anomaly_score": anomaly_score
                }
            )
            
            db.session.add(alert)
            db.session.commit()
            
            logger.info("Создан алерт об аномалии", alert_id=alert.id, database_id=database_id)
            
        except Exception as exc:
            logger.error("Ошибка при создании алерта об аномалии", error=str(exc))
            db.session.rollback()
    
    def _analyze_performance_trends(self, database_id: int) -> List[Dict[str, Any]]:
        """
        Анализ трендов производительности
        """
        try:
            recommendations = []
            
            # Получаем метрики за последние 24 часа
            since = datetime.now() - timedelta(hours=24)
            metrics = DatabaseMetric.query.filter(
                DatabaseMetric.database_id == database_id,
                DatabaseMetric.timestamp >= since
            ).order_by(DatabaseMetric.timestamp).all()
            
            if len(metrics) < 10:
                return recommendations
            
            # Анализ тренда CPU
            cpu_values = [m.cpu_usage for m in metrics if m.cpu_usage is not None]
            if len(cpu_values) >= 10:
                cpu_trend = np.polyfit(range(len(cpu_values)), cpu_values, 1)[0]
                if cpu_trend > 2:  # Рост более 2% в час
                    recommendations.append({
                        "type": "trend",
                        "priority": "medium",
                        "title": "Растущая нагрузка на CPU",
                        "description": f"CPU нагрузка растет со скоростью {cpu_trend:.1f}% в час",
                        "category": "resource_monitoring",
                        "impact": "medium",
                        "effort": "low"
                    })
            
            # Анализ тренда памяти
            memory_values = [m.memory_usage for m in metrics if m.memory_usage is not None]
            if len(memory_values) >= 10:
                memory_trend = np.polyfit(range(len(memory_values)), memory_values, 1)[0]
                if memory_trend > 1:  # Рост более 1% в час
                    recommendations.append({
                        "type": "trend",
                        "priority": "medium",
                        "title": "Растущее потребление памяти",
                        "description": f"Потребление памяти растет со скоростью {memory_trend:.1f}% в час",
                        "category": "memory_management",
                        "impact": "medium",
                        "effort": "medium"
                    })
            
            return recommendations
            
        except Exception as exc:
            logger.error("Ошибка при анализе трендов", database_id=database_id, error=str(exc))
            return []

# Глобальный экземпляр анализатора
performance_analyzer = OptimizedPerformanceAnalyzer()

