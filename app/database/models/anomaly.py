"""
Anomaly result database model.

Stores anomaly detection results for historical analysis.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, DateTime, Boolean, Float, String, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database.base import Base


class AnomalyResult(Base):
    """
    Anomaly result model for storing detection outcomes.
    
    Separate table from telemetry for query performance since anomalies
    are typically sparse compared to normal telemetry.
    """
    __tablename__ = "anomaly_results"
    
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Anomaly result identifier"
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
        comment="Anomaly check timestamp"
    )
    is_anomaly = Column(
        Boolean,
        nullable=False,
        index=True,
        comment="Whether an anomaly was detected"
    )
    anomaly_score = Column(
        Float,
        nullable=True,
        comment="Anomaly score [0-1], None for rule-based detection"
    )
    model_name = Column(
        String(100),
        nullable=False,
        comment="Detection model name"
    )
    detection_metadata = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional detection context"
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Record creation timestamp"
    )
    
    # Relationships
    service = relationship("Service", back_populates="anomaly_results")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            'anomaly_score IS NULL OR (anomaly_score >= 0 AND anomaly_score <= 1)',
            name='ck_anomaly_score_range'
        ),
        # Composite index for time-range queries per service
        Index('idx_anomaly_service_timestamp', 'service_id', 'timestamp'),
        # Partial index for efficient anomaly-only queries
        Index('idx_anomaly_is_anomaly', 'is_anomaly', postgresql_where=(Column('is_anomaly') == True)),
    )
    
    def __repr__(self) -> str:
        return f"<AnomalyResult(id={self.id}, service_id={self.service_id}, is_anomaly={self.is_anomaly})>"
