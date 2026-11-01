"""
Isolation Forest Detector - ML-based anomaly detection.

Uses scikit-learn's Isolation Forest algorithm to detect anomalies
in telemetry data. Handles training, inference, and model persistence.
"""

from typing import Optional, Dict, Any
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.ml.detectors.base_detector import BaseDetector, AnomalyDetectionResult
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.exceptions import ModelNotFoundException

logger = get_logger(__name__)
settings = get_settings()


class IsolationForestDetector(BaseDetector):
    """
    Isolation Forest anomaly detector.
    
    Key concepts:
    - Isolation Forest doesn't produce probability scores
    - decision_function() returns anomaly scores (lower = more anomalous)
    - We normalize scores to [0, 1] where higher = more anomalous
    - Uses StandardScaler for feature normalization
    """
    
    def __init__(
        self,
        name: str = "isolation_forest",
        contamination: Optional[float] = None,
        n_estimators: Optional[int] = None,
        random_state: Optional[int] = None
    ):
        """
        Initialize Isolation Forest detector.
        
        Args:
            name: Detector name
            contamination: Expected proportion of anomalies [0, 0.5]
            n_estimators: Number of trees
            random_state: Random seed for reproducibility
        """
        super().__init__(name)
        
        # Use config defaults if not provided
        self.contamination = contamination or settings.ISOLATION_FOREST_CONTAMINATION
        self.n_estimators = n_estimators or settings.ISOLATION_FOREST_N_ESTIMATORS
        self.random_state = random_state or settings.ISOLATION_FOREST_RANDOM_STATE
        
        # Initialize model and scaler
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        
        # Track training statistics for score normalization
        self.score_min: Optional[float] = None
        self.score_max: Optional[float] = None
        
        logger.info(
            f"Initialized {self.name} with contamination={self.contamination}, "
            f"n_estimators={self.n_estimators}, random_state={self.random_state}"
        )
    
    def train(self, features: np.ndarray) -> Dict[str, Any]:
        """
        Train the Isolation Forest model.
        
        Args:
            features: Training feature matrix of shape (n_samples, n_features)
        
        Returns:
            Dict with training statistics
        """
        logger.info(f"Training {self.name} on {features.shape[0]} samples...")
        
        # Initialize scaler and normalize features
        self.scaler = StandardScaler()
        features_scaled = self.scaler.fit_transform(features)
        
        # Initialize and train model
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=-1  # Use all CPU cores
        )
        
        self.model.fit(features_scaled)
        
        # Compute score statistics for normalization
        scores = self.model.decision_function(features_scaled)
        self.score_min = float(scores.min())
        self.score_max = float(scores.max())
        
        # Training statistics
        predictions = self.model.predict(features_scaled)
        n_anomalies = np.sum(predictions == -1)
        
        stats = {
            "n_samples": features.shape[0],
            "n_features": features.shape[1],
            "n_anomalies_in_training": int(n_anomalies),
            "anomaly_rate": float(n_anomalies / features.shape[0]),
            "score_range": (self.score_min, self.score_max)
        }
        
        logger.info(f"Training complete: {stats}")
        return stats
    
    def detect(self, features: np.ndarray) -> AnomalyDetectionResult:
        """
        Detect anomalies using trained Isolation Forest.
        
        Args:
            features: Feature vector or matrix
        
        Returns:
            AnomalyDetectionResult
        
        Raises:
            ModelNotFoundException: If model not trained
        """
        if not self.is_trained():
            raise ModelNotFoundException(self.name)
        
        # Handle single sample
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Predict
        predictions = self.model.predict(features_scaled)
        raw_scores = self.model.decision_function(features_scaled)
        
        # For single sample
        if len(predictions) == 1:
            is_anomaly = bool(predictions[0] == -1)
            raw_score = float(raw_scores[0])
            
            # Normalize score to [0, 1]
            # Isolation Forest: lower scores = more anomalous
            # We invert and normalize: higher scores = more anomalous
            normalized_score = self._normalize_score(raw_score)
            
            metadata = {
                "raw_score": raw_score,
                "normalized_score": normalized_score,
                "prediction": int(predictions[0]),
                "feature_values": features[0].tolist(),
                "score_range": (self.score_min, self.score_max)
            }
            
            if is_anomaly:
                logger.info(
                    f"Isolation Forest anomaly detected: "
                    f"score={normalized_score:.3f}, raw_score={raw_score:.3f}"
                )
            
            return AnomalyDetectionResult(
                is_anomaly=is_anomaly,
                anomaly_score=normalized_score,
                model_name=self.name,
                detection_metadata=metadata
            )
        
        # Batch prediction - return result for last sample
        logger.warning("Batch detection - returning result for last sample")
        is_anomaly = bool(predictions[-1] == -1)
        raw_score = float(raw_scores[-1])
        normalized_score = self._normalize_score(raw_score)
        
        metadata = {
            "raw_score": raw_score,
            "normalized_score": normalized_score,
            "batch_size": len(predictions),
            "batch_anomalies": int(np.sum(predictions == -1))
        }
        
        return AnomalyDetectionResult(
            is_anomaly=is_anomaly,
            anomaly_score=normalized_score,
            model_name=self.name,
            detection_metadata=metadata
        )
    
    def _normalize_score(self, raw_score: float) -> float:
        """
        Normalize Isolation Forest score to [0, 1].
        
        Isolation Forest decision_function():
        - Lower (more negative) values = more anomalous
        - Higher (more positive) values = more normal
        
        Our normalized score:
        - 0.0 = completely normal
        - 1.0 = highly anomalous
        
        Args:
            raw_score: Raw Isolation Forest decision function output
        
        Returns:
            float: Normalized score in [0, 1]
        """
        if self.score_min is None or self.score_max is None:
            # Fallback if statistics not available
            return 0.5
        
        # Invert: make lower scores → higher normalized values
        # Then scale to [0, 1]
        if self.score_max == self.score_min:
            return 0.5
        
        # Map: [score_max, score_min] → [0, 1]
        normalized = (self.score_max - raw_score) / (self.score_max - self.score_min)
        
        # Clamp to [0, 1]
        return float(np.clip(normalized, 0.0, 1.0))
    
    def is_trained(self) -> bool:
        """
        Check if model is trained.
        
        Returns:
            bool: True if model and scaler are available
        """
        return self.model is not None and self.scaler is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.
        
        Returns:
            Dict with model parameters and statistics
        """
        if not self.is_trained():
            return {"trained": False}
        
        return {
            "trained": True,
            "contamination": self.contamination,
            "n_estimators": self.n_estimators,
            "random_state": self.random_state,
            "score_range": (self.score_min, self.score_max),
            "n_features": self.model.n_features_in_
        }
