"""
Rule-Based Detector - Threshold-based baseline anomaly detection.

This detector uses simple configurable thresholds to identify anomalies.
It serves as a baseline for comparing ML model performance and handles
the cold-start problem before sufficient training data is available.
"""

from typing import Dict, Any, List
import numpy as np

from app.ml.detectors.base_detector import BaseDetector, AnomalyDetectionResult
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RuleBasedDetector(BaseDetector):
    """
    Rule-based anomaly detector using configurable thresholds.
    
    Detects anomalies when any metric exceeds its threshold:
    - CPU usage > threshold
    - Memory usage > threshold
    - Error rate > threshold
    - P95 latency > threshold
    
    Request rate is informational only (no threshold by default).
    """
    
    def __init__(self, name: str = "rule_based_baseline"):
        """
        Initialize rule-based detector.
        
        Thresholds are loaded from configuration.
        """
        super().__init__(name)
        
        # Load thresholds from config
        self.thresholds = {
            "cpu_usage_percent": settings.RULE_CPU_THRESHOLD,
            "memory_usage_percent": settings.RULE_MEMORY_THRESHOLD,
            "error_rate_percent": settings.RULE_ERROR_RATE_THRESHOLD,
            "p95_latency_ms": settings.RULE_LATENCY_THRESHOLD
        }
        
        logger.info(f"Initialized {self.name} with thresholds: {self.thresholds}")
    
    def detect(self, features: np.ndarray) -> AnomalyDetectionResult:
        """
        Detect anomalies using threshold rules.
        
        Args:
            features: Feature vector [cpu, memory, request_rate, error_rate, latency]
        
        Returns:
            AnomalyDetectionResult with triggered rules in metadata
        """
        # Handle single sample
        if features.ndim == 1:
            return self._detect_single(features)
        
        # For batch, detect on the most recent sample
        logger.warning("Batch detection with rule-based detector - using last sample")
        return self._detect_single(features[-1])
    
    def _detect_single(self, features: np.ndarray) -> AnomalyDetectionResult:
        """
        Detect anomalies in a single feature vector.
        
        Args:
            features: Feature vector of shape (5,)
        
        Returns:
            AnomalyDetectionResult
        """
        cpu, memory, request_rate, error_rate, latency = features
        
        # Check each rule
        triggered_rules = []
        
        if cpu > self.thresholds["cpu_usage_percent"]:
            triggered_rules.append({
                "rule": "high_cpu",
                "value": float(cpu),
                "threshold": self.thresholds["cpu_usage_percent"]
            })
        
        if memory > self.thresholds["memory_usage_percent"]:
            triggered_rules.append({
                "rule": "high_memory",
                "value": float(memory),
                "threshold": self.thresholds["memory_usage_percent"]
            })
        
        if error_rate > self.thresholds["error_rate_percent"]:
            triggered_rules.append({
                "rule": "high_error_rate",
                "value": float(error_rate),
                "threshold": self.thresholds["error_rate_percent"]
            })
        
        if latency > self.thresholds["p95_latency_ms"]:
            triggered_rules.append({
                "rule": "high_latency",
                "value": float(latency),
                "threshold": self.thresholds["p95_latency_ms"]
            })
        
        # Determine if anomaly
        is_anomaly = len(triggered_rules) > 0
        
        # Build metadata
        metadata = {
            "triggered_rules": triggered_rules,
            "rule_count": len(triggered_rules),
            "thresholds": self.thresholds,
            "feature_values": {
                "cpu_usage_percent": float(cpu),
                "memory_usage_percent": float(memory),
                "request_rate": float(request_rate),
                "error_rate_percent": float(error_rate),
                "p95_latency_ms": float(latency)
            }
        }
        
        if is_anomaly:
            logger.info(
                f"Rule-based anomaly detected: {len(triggered_rules)} rule(s) triggered"
            )
        
        return AnomalyDetectionResult(
            is_anomaly=is_anomaly,
            anomaly_score=None,  # Rule-based doesn't produce scores
            model_name=self.name,
            detection_metadata=metadata
        )
    
    def is_trained(self) -> bool:
        """
        Rule-based detector doesn't require training.
        
        Returns:
            bool: Always True
        """
        return True
    
    def update_thresholds(self, new_thresholds: Dict[str, float]) -> None:
        """
        Update detection thresholds dynamically.
        
        Args:
            new_thresholds: Dictionary with new threshold values
        """
        self.thresholds.update(new_thresholds)
        logger.info(f"Updated thresholds: {self.thresholds}")
    
    def get_thresholds(self) -> Dict[str, float]:
        """
        Get current thresholds.
        
        Returns:
            Dict[str, float]: Current thresholds
        """
        return self.thresholds.copy()
