"""
Pydantic schemas for Incident entities.

These schemas define the API contract for incident management.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class IncidentStatus(str, Enum):
    """Incident lifecycle status"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class IncidentSeverity(str, Enum):
    """
    Incident severity levels.
    
    Severity is determined based on anomaly score and affected metrics.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentBase(BaseModel):
    """Base incident attributes"""
    service_id: UUID = Field(..., description="Service identifier")
    severity: IncidentSeverity = Field(..., description="Incident severity")


class IncidentCreate(IncidentBase):
    """
    Schema for creating incidents.
    
    Incidents are typically created automatically by the anomaly detection pipeline.
    """
    anomaly_score: Optional[float] = Field(
        default=None,
        description="Anomaly score that triggered the incident (if applicable)"
    )
    detection_model: str = Field(
        ...,
        max_length=100,
        description="Name of the detection model that triggered the incident"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional incident context"
    )


class IncidentUpdate(BaseModel):
    """
    Schema for updating incidents.
    
    Allows updating status, severity, and metadata.
    """
    status: Optional[IncidentStatus] = Field(
        default=None,
        description="Updated incident status"
    )
    severity: Optional[IncidentSeverity] = Field(
        default=None,
        description="Updated incident severity"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated metadata"
    )


class IncidentResponse(IncidentBase):
    """Schema for incident API responses"""
    id: UUID = Field(..., description="Unique incident identifier")
    status: IncidentStatus = Field(..., description="Current incident status")
    anomaly_score: Optional[float] = Field(..., description="Anomaly score")
    detection_model: str = Field(..., description="Detection model")
    meta: Dict[str, Any] = Field(..., description="Incident metadata")
    created_at: datetime = Field(..., description="Incident creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    resolved_at: Optional[datetime] = Field(..., description="Resolution timestamp (if resolved)")
    
    model_config = ConfigDict(from_attributes=True)


class IncidentQueryParams(BaseModel):
    """
    Query parameters for fetching incidents.
    
    Supports filtering by status, severity, and pagination.
    """
    status: Optional[IncidentStatus] = Field(
        default=None,
        description="Filter by incident status"
    )
    severity: Optional[IncidentSeverity] = Field(
        default=None,
        description="Filter by incident severity"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of incidents to return"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of incidents to skip"
    )
