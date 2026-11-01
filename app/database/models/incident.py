"""
Incident database model.

Stores incidents created by anomaly detection.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database.base import Base


class Incident(Base):
    """
    Incident model representing anomaly-triggered incidents.
    
    Incidents track abnormal service behavior detected by the anomaly detection system.
    """
    __tablename__ = "incidents"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique incident identifier"
    )
    service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        comment="Service identifier"
    )
    status = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Incident status (open, investigating, resolved)"
    )
    severity = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Incident severity (low, medium, high, critical)"
    )
    anomaly_score = Column(
        Float,
        nullable=True,
        comment="Anomaly score that triggered the incident"
    )
    detection_model = Column(
        String(100),
        nullable=False,
        comment="Detection model that triggered the incident"
    )
    meta = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional incident context"
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
        comment="Incident creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Last update timestamp"
    )
    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Resolution timestamp (if resolved)"
    )
    
    # Relationships
    service = relationship("Service", back_populates="incidents")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            'anomaly_score IS NULL OR (anomaly_score >= 0 AND anomaly_score <= 1)',
            name='ck_incident_anomaly_score_range'
        ),
        # Composite index for finding open incidents per service
        Index('idx_incidents_service_status', 'service_id', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<Incident(id={self.id}, service_id={self.service_id}, status={self.status}, severity={self.severity})>"
