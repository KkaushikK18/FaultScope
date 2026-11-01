"""
Pydantic schemas for Anomaly detection results.

These schemas define the output format for both rule-based and ML-based
anomaly detectors.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class AnomalyResultBase(BaseModel):
    """
    Base anomaly detection result.
    
    All detectors (rule-based and ML-based) must produce this format.
    """
    service_id: UUID = Field(..., description="Service identifier")
    timestamp: datetime = Field(..., description="Timestamp of the anomaly check")
    is_anomaly: bool = Field(..., description="Whether an anomaly was detected")
    model_name: str = Field(..., max_length=100, description="Name of the detection model used")


class AnomalyResultCreate(AnomalyResultBase):
    """
    Schema for persisting anomaly results.
    
    Note: anomaly_score is optional because rule-based detectors may not produce scores.
    For ML models, the score should be normalized to [0, 1] where higher values
    indicate stronger anomaly signals.
    """
    anomaly_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Anomaly score [0, 1] - higher means more anomalous. None for rule-based detection."
    )
    detection_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional detection context (e.g., which rules triggered, feature importances)"
    )


class AnomalyResultResponse(AnomalyResultBase):
    """Schema for anomaly API responses"""
    id: int = Field(..., description="Anomaly result identifier")
    anomaly_score: Optional[float] = Field(..., description="Anomaly score (None if not applicable)")
    detection_metadata: Dict[str, Any] = Field(..., description="Detection metadata")
    created_at: datetime = Field(..., description="When the anomaly was recorded")
    
    model_config = ConfigDict(from_attributes=True)


class AnomalyQueryParams(BaseModel):
    """
    Query parameters for fetching anomaly results.
    
    Supports time-range filtering and pagination.
    """
    start_time: Optional[datetime] = Field(
        default=None,
        description="Filter anomalies after this timestamp"
    )
    end_time: Optional[datetime] = Field(
        default=None,
        description="Filter anomalies before this timestamp"
    )
    anomalies_only: bool = Field(
        default=True,
        description="If True, only return records where is_anomaly=True"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of records to return"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip"
    )
