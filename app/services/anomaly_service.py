"""
Anomaly Service - Business logic for anomaly detection and management.

Orchestrates the anomaly detection pipeline:
1. Extract features from telemetry
2. Run detection (rule-based or ML)
3. Persist anomaly results
4. Query historical anomalies
"""

from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.models.anomaly import AnomalyResult
from app.database.models.telemetry import TelemetryRecord
from app.schemas.anomaly import AnomalyResultCreate, AnomalyQueryParams
from app.ml.features.feature_extractor import FeatureExtractor
from app.ml.detectors.base_detector import BaseDetector
from app.ml.detectors.rule_based import RuleBasedDetector
from app.ml.detectors.isolation_forest import IsolationForestDetector
from app.ml.model_loader import ModelLoader
from app.core.exceptions import ServiceNotFoundException, ModelNotFoundException
from app.core.logging import get_logger
from app.services.service_manager import ServiceManager
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class AnomalyService:
    """
    Service for anomaly detection operations.
    
    Manages detector selection, anomaly detection, and result persistence.
    """
    
    def __init__(self, db: Session):
        """
        Initialize anomaly service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.service_manager = ServiceManager(db)
        self.feature_extractor = FeatureExtractor()
        self.model_loader = ModelLoader()
        
        # Initialize detectors
        self.rule_detector = RuleBasedDetector()
        self.ml_detector: Optional[IsolationForestDetector] = None
        
        # Try to load ML model
        self._load_ml_model()
    
    def _load_ml_model(self) -> None:
        """Attempt to load the latest trained ML model."""
        try:
            self.ml_detector = self.model_loader.load_isolation_forest(use_latest=True)
            logger.info("Successfully loaded ML detector")
        except ModelNotFoundException:
            logger.warning("No trained ML model found - using rule-based detector only")
            self.ml_detector = None
    
    def detect_from_telemetry(
        self,
        telemetry: TelemetryRecord,
        use_ml: bool = True
    ) -> AnomalyResult:
        """
        Detect anomalies from a telemetry record and persist result.
        
        Args:
            telemetry: TelemetryRecord to analyze
            use_ml: If True, use ML detector if available; otherwise use rule-based
        
        Returns:
            AnomalyResult: Persisted anomaly result
        """
        # Extract features
        features = self.feature_extractor.extract_from_telemetry(telemetry)
        
        # Select detector
        detector = self._select_detector(use_ml)
        
        # Run detection
        result = detector.detect(features)
        
        # Create anomaly result
        anomaly_data = AnomalyResultCreate(
            service_id=telemetry.service_id,
            timestamp=telemetry.timestamp,
            is_anomaly=result.is_anomaly,
            anomaly_score=result.anomaly_score,
            model_name=result.model_name,
            detection_metadata=result.detection_metadata
        )
        
        # Persist
        anomaly_result = self._persist_anomaly_result(anomaly_data)
        
        if result.is_anomaly:
            logger.info(
                f"Anomaly detected for service {telemetry.service_id} "
                f"using {detector.get_name()}"
            )
        
        return anomaly_result
    
    def _select_detector(self, use_ml: bool) -> BaseDetector:
        """
        Select appropriate detector based on availability and preference.
        
        Args:
            use_ml: Prefer ML detector if available
        
        Returns:
            BaseDetector: Selected detector
        """
        if use_ml and self.ml_detector and self.ml_detector.is_trained():
            return self.ml_detector
        
        logger.info("Using rule-based detector")
        return self.rule_detector
    
    def _persist_anomaly_result(
        self,
        anomaly_data: AnomalyResultCreate
    ) -> AnomalyResult:
        """
        Persist anomaly result to database.
        
        Args:
            anomaly_data: Anomaly result data
        
        Returns:
            AnomalyResult: Persisted result
        """
        anomaly = AnomalyResult(
            service_id=anomaly_data.service_id,
            timestamp=anomaly_data.timestamp,
            is_anomaly=anomaly_data.is_anomaly,
            anomaly_score=anomaly_data.anomaly_score,
            model_name=anomaly_data.model_name,
            detection_metadata=anomaly_data.detection_metadata or {}
        )
        
        self.db.add(anomaly)
        self.db.commit()
        self.db.refresh(anomaly)
        
        return anomaly
    
    def query_anomalies(
        self,
        service_id: UUID,
        params: AnomalyQueryParams
    ) -> List[AnomalyResult]:
        """
        Query anomaly results for a service.
        
        Args:
            service_id: Service UUID
            params: Query parameters
        
        Returns:
            List[AnomalyResult]: Anomaly results
        
        Raises:
            ServiceNotFoundException: If service doesn't exist
        """
        # Validate service exists
        self.service_manager.get_service_by_id(service_id)
        
        # Build query
        query = self.db.query(AnomalyResult).filter(
            AnomalyResult.service_id == service_id
        )
        
        # Filter by anomalies only if requested
        if params.anomalies_only:
            query = query.filter(AnomalyResult.is_anomaly == True)
        
        # Apply time filters
        if params.start_time:
            query = query.filter(AnomalyResult.timestamp >= params.start_time)
        
        if params.end_time:
            query = query.filter(AnomalyResult.timestamp <= params.end_time)
        
        # Order by timestamp (most recent first)
        query = query.order_by(desc(AnomalyResult.timestamp))
        
        # Apply pagination
        results = query.offset(params.offset).limit(params.limit).all()
        
        logger.info(
            f"Retrieved {len(results)} anomaly results for service {service_id}"
        )
        return results
    
    def count_anomalies(
        self,
        service_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        anomalies_only: bool = True
    ) -> int:
        """
        Count anomaly results for a service.
        
        Args:
            service_id: Service UUID
            start_time: Optional start time filter
            end_time: Optional end time filter
            anomalies_only: If True, count only detected anomalies
        
        Returns:
            int: Number of anomaly results
        """
        query = self.db.query(AnomalyResult).filter(
            AnomalyResult.service_id == service_id
        )
        
        if anomalies_only:
            query = query.filter(AnomalyResult.is_anomaly == True)
        
        if start_time:
            query = query.filter(AnomalyResult.timestamp >= start_time)
        
        if end_time:
            query = query.filter(AnomalyResult.timestamp <= end_time)
        
        return query.count()
    
    def get_detector_info(self) -> dict:
        """
        Get information about available detectors.
        
        Returns:
            dict: Detector information
        """
        info = {
            "rule_based": {
                "available": True,
                "trained": self.rule_detector.is_trained(),
                "name": self.rule_detector.get_name(),
                "thresholds": self.rule_detector.get_thresholds()
            },
            "ml_based": {
                "available": self.ml_detector is not None,
                "trained": self.ml_detector.is_trained() if self.ml_detector else False,
                "name": self.ml_detector.get_name() if self.ml_detector else None,
                "info": self.ml_detector.get_model_info() if self.ml_detector else None
            }
        }
        
        return info
    
    def reload_ml_model(self) -> bool:
        """
        Reload the ML model from disk.
        
        Useful after training a new model.
        
        Returns:
            bool: True if model loaded successfully
        """
        try:
            self._load_ml_model()
            return self.ml_detector is not None
        except Exception as e:
            logger.error(f"Failed to reload ML model: {e}")
            return False
