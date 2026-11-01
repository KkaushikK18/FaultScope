"""
Service database model.

Represents a monitored application service.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database.base import Base


class Service(Base):
    """
    Service model representing a monitored application service.
    
    Each service is uniquely identified by (service_name, environment) combination.
    """
    __tablename__ = "services"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique service identifier"
    )
    service_name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Service name"
    )
    environment = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Deployment environment (e.g., production, staging, local)"
    )
    status = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Service health status"
    )
    meta = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional service metadata"
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Service registration timestamp"
    )
    
    # Relationships
    telemetry_records = relationship(
        "TelemetryRecord",
        back_populates="service",
        cascade="all, delete-orphan"
    )
    anomaly_results = relationship(
        "AnomalyResult",
        back_populates="service",
        cascade="all, delete-orphan"
    )
    incidents = relationship(
        "Incident",
        back_populates="service",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('service_name', 'environment', name='uq_service_name_env'),
    )
    
    def __repr__(self) -> str:
        return f"<Service(id={self.id}, name={self.service_name}, env={self.environment})>"
