"""
Pydantic schemas for Telemetry entities.

These schemas define the normalized telemetry format and validation rules.
All telemetry, regardless of source, must conform to this structure.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict


class TelemetryRecordBase(BaseModel):
    """
    Base telemetry attributes.
    
    This represents the normalized telemetry format used internally.
    All metrics are validated to ensure data quality.
    """
    service_id: UUID = Field(..., description="Service identifier")
    timestamp: datetime = Field(..., description="Telemetry timestamp (timezone-aware)")
    cpu_usage_percent: float = Field(..., ge=0.0, le=100.0, description="CPU usage percentage")
    memory_usage_percent: float = Field(..., ge=0.0, le=100.0, description="Memory usage percentage")
    request_rate: float = Field(..., ge=0.0, description="Request rate (requests/second)")
    error_rate_percent: float = Field(..., ge=0.0, le=100.0, description="Error rate percentage")
    p95_latency_ms: float = Field(..., ge=0.0, description="P95 latency in milliseconds")
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """
        Ensure timestamp is timezone-aware.
        
        Timezone-aware timestamps prevent ambiguity in distributed systems
        where telemetry may come from multiple time zones.
        """
        if v.tzinfo is None:
            raise ValueError('Timestamp must be timezone-aware (include timezone info)')
        return v


class TelemetryRecordCreate(TelemetryRecordBase):
    """
    Schema for ingesting telemetry via API.
    
    Includes optional fields for tracking telemetry source and additional labels.
    """
    source: Optional[str] = Field(
        default="api",
        max_length=50,
        description="Telemetry source (e.g., 'prometheus', 'api', 'custom')"
    )
    labels: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional labels/tags for the telemetry"
    )


class TelemetryRecordResponse(TelemetryRecordBase):
    """Schema for telemetry API responses"""
    id: int = Field(..., description="Telemetry record identifier")
    source: str = Field(..., description="Telemetry source")
    labels: Dict[str, Any] = Field(..., description="Additional labels")
    
    model_config = ConfigDict(from_attributes=True)


class TelemetryQueryParams(BaseModel):
    """
    Query parameters for fetching telemetry records.
    
    Supports time-range filtering and pagination.
    """
    start_time: Optional[datetime] = Field(
        default=None,
        description="Filter telemetry after this timestamp"
    )
    end_time: Optional[datetime] = Field(
        default=None,
        description="Filter telemetry before this timestamp"
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
