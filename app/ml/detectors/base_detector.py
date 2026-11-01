"""
Base Detector - Abstract interface for all anomaly detectors.

This provides a consistent interface that both rule-based and ML-based
detectors must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np
from pydantic import BaseModel, ConfigDict
from dataclasses import dataclass


@dataclass
class AnomalyDetectionResult:
    """
    Structured result from anomaly detection.
    
    Attributes:
        is_anomaly: Whether an anomaly was detected
        anomaly_score: Normalized score [0, 1] or None for rule-based
        model_name: Name of the detector that generated this result
        detection_metadata: Additional context about the detection
    """
    is_anomaly: bool
    anomaly_score: Optional[float]
    model_name: str
    detection_metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "is_anomaly": self.is_anomaly,
            "anomaly_score": self.anomaly_score,
            "model_name": self.model_name,
            "detection_metadata": self.detection_metadata
        }


class BaseDetector(ABC):
    """
    Abstract base class for anomaly detectors.
    
    All detectors (rule-based, ML-based, etc.) must inherit from this
    class and implement the detect() method.
    """
    
    def __init__(self, name: str):
        """
        Initialize detector.
        
        Args:
            name: Unique name for this detector
        """
        self.name = name
    
    @abstractmethod
    def detect(self, features: np.ndarray) -> AnomalyDetectionResult:
        """
        Detect anomalies in feature vector(s).
        
        Args:
            features: Feature array of shape (n_features,) for single sample
                     or (n_samples, n_features) for batch
        
        Returns:
            AnomalyDetectionResult: Detection result
        """
        pass
    
    @abstractmethod
    def is_trained(self) -> bool:
        """
        Check if detector is trained and ready for inference.
        
        Returns:
            bool: True if ready, False otherwise
        """
        pass
    
    def get_name(self) -> str:
        """Get detector name."""
        return self.name
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
