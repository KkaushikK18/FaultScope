"""
Telemetry database model.

Stores normalized telemetry records from all services.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, DateTime, Float, String, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database.base import Base


class TelemetryRecord(Base):
    """
    Telemetry record model for storing service metrics.
    
    This table stores high-volume time-series data with appropriate indexing
    for efficient time-based and service-based queries.
    """
    __tablename__ = "telemetry_records"
    
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Telemetry record identifier"
    )
    service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        comment="Service identifier"
    )
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Telemetry timestamp"
    )
    cpu_usage_percent = Column(
        Float,
        nullable=False,
        comment="CPU usage percentage [0-100]"
    )
    memory_usage_percent = Column(
        Float,
        nullable=False,
        comment="Memory usage percentage [0-100]"
    )
    request_rate = Column(
        Float,
        nullable=False,
        comment="Request rate (requests/second)"
    )
    error_rate_percent = Column(
        Float,
        nullable=False,
        comment="Error rate percentage [0-100]"
    )
    p95_latency_ms = Column(
        Float,
        nullable=False,
        comment="P95 latency in milliseconds"
    )
    source = Column(
        String(50),
        nullable=False,
        default="api",
        comment="Telemetry source (e.g., prometheus, api)"
    )
    labels = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional labels/tags"
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Record creation timestamp"
    )
    
    # Relationships
    service = relationship("Service", back_populates="telemetry_records")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('cpu_usage_percent >= 0 AND cpu_usage_percent <= 100', name='ck_cpu_range'),
        CheckConstraint('memory_usage_percent >= 0 AND memory_usage_percent <= 100', name='ck_memory_range'),
        CheckConstraint('request_rate >= 0', name='ck_request_rate_positive'),
        CheckConstraint('error_rate_percent >= 0 AND error_rate_percent <= 100', name='ck_error_rate_range'),
        CheckConstraint('p95_latency_ms >= 0', name='ck_latency_positive'),
        # Composite index for efficient time-range queries per service
        Index('idx_telemetry_service_timestamp', 'service_id', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        return f"<TelemetryRecord(id={self.id}, service_id={self.service_id}, timestamp={self.timestamp})>"
