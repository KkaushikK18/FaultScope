"""
Feature Extractor - Converts telemetry records into ML feature vectors.

This module provides a clean abstraction layer between raw telemetry data
and ML models, making it easy to add derived features in the future.
"""

from typing import List, Dict, Any
import numpy as np
from app.database.models.telemetry import TelemetryRecord
from app.core.logging import get_logger

logger = get_logger(__name__)


class FeatureExtractor:
    """
    Extracts feature vectors from telemetry records.
    
    For v0.1, we use the 5 core metrics directly:
    - cpu_usage_percent
    - memory_usage_percent
    - request_rate
    - error_rate_percent
    - p95_latency_ms
    
    Future enhancements can add derived features like:
    - Rolling averages
    - Rate of change
    - Statistical moments
    - Cross-metric ratios
    """
    
    # Feature names in order (important for consistency)
    FEATURE_NAMES = [
        "cpu_usage_percent",
        "memory_usage_percent",
        "request_rate",
        "error_rate_percent",
        "p95_latency_ms"
    ]
    
    @staticmethod
    def extract_from_telemetry(telemetry: TelemetryRecord) -> np.ndarray:
        """
        Extract feature vector from a single telemetry record.
        
        Args:
            telemetry: TelemetryRecord instance
            
        Returns:
            np.ndarray: Feature vector of shape (5,)
        """
        features = np.array([
            telemetry.cpu_usage_percent,
            telemetry.memory_usage_percent,
            telemetry.request_rate,
            telemetry.error_rate_percent,
            telemetry.p95_latency_ms
        ], dtype=np.float32)
        
        return features
    
    @staticmethod
    def extract_from_dict(data: Dict[str, Any]) -> np.ndarray:
        """
        Extract feature vector from dictionary (useful for API inputs).
        
        Args:
            data: Dictionary with telemetry fields
            
        Returns:
            np.ndarray: Feature vector of shape (5,)
        """
        features = np.array([
            data["cpu_usage_percent"],
            data["memory_usage_percent"],
            data["request_rate"],
            data["error_rate_percent"],
            data["p95_latency_ms"]
        ], dtype=np.float32)
        
        return features
    
    @staticmethod
    def extract_batch(telemetry_records: List[TelemetryRecord]) -> np.ndarray:
        """
        Extract feature matrix from multiple telemetry records.
        
        Args:
            telemetry_records: List of TelemetryRecord instances
            
        Returns:
            np.ndarray: Feature matrix of shape (n_records, 5)
        """
        if not telemetry_records:
            return np.array([]).reshape(0, 5)
        
        features = np.array([
            [
                record.cpu_usage_percent,
                record.memory_usage_percent,
                record.request_rate,
                record.error_rate_percent,
                record.p95_latency_ms
            ]
            for record in telemetry_records
        ], dtype=np.float32)
        
        logger.info(f"Extracted features from {len(telemetry_records)} telemetry records")
        return features
    
    @staticmethod
    def get_feature_names() -> List[str]:
        """
        Get ordered list of feature names.
        
        Returns:
            List[str]: Feature names
        """
        return FeatureExtractor.FEATURE_NAMES.copy()
    
    @staticmethod
    def validate_features(features: np.ndarray) -> bool:
        """
        Validate feature vector shape and values.
        
        Args:
            features: Feature array to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Check shape
        if features.ndim == 1:
            if features.shape[0] != 5:
                logger.error(f"Invalid feature vector shape: {features.shape}, expected (5,)")
                return False
        elif features.ndim == 2:
            if features.shape[1] != 5:
                logger.error(f"Invalid feature matrix shape: {features.shape}, expected (*, 5)")
                return False
        else:
            logger.error(f"Invalid feature dimensions: {features.ndim}, expected 1 or 2")
            return False
        
        # Check for NaN or Inf
        if np.any(np.isnan(features)) or np.any(np.isinf(features)):
            logger.error("Features contain NaN or Inf values")
            return False
        
        return True
