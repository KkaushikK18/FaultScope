"""
Telemetry Service - Business logic for telemetry ingestion and queries.

Handles telemetry normalization, validation, persistence, and retrieval.
"""

from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.models.telemetry import TelemetryRecord
from app.schemas.telemetry import TelemetryRecordCreate, TelemetryQueryParams
from app.core.exceptions import ServiceNotFoundException, InvalidTelemetryException
from app.core.logging import get_logger
from app.services.service_manager import ServiceManager

logger = get_logger(__name__)


class TelemetryService:
    """
    Service class for telemetry operations.
    
    Encapsulates telemetry ingestion, normalization, and query logic.
    """
    
    def __init__(self, db: Session):
        """
        Initialize telemetry service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.service_manager = ServiceManager(db)
    
    def ingest_telemetry(self, telemetry_data: TelemetryRecordCreate) -> TelemetryRecord:
        """
        Ingest and store telemetry record.
        
        This method:
        1. Validates that the service exists
        2. Normalizes the telemetry data
        3. Persists to database
        
        Args:
            telemetry_data: Telemetry record data
            
        Returns:
            TelemetryRecord: Stored telemetry record
            
        Raises:
            ServiceNotFoundException: If service doesn't exist
            InvalidTelemetryException: If telemetry data is invalid
        """
        logger.info(f"Ingesting telemetry for service {telemetry_data.service_id}")
        
        # Validate service exists
        try:
            self.service_manager.get_service_by_id(telemetry_data.service_id)
        except ServiceNotFoundException:
            logger.error(f"Cannot ingest telemetry: service {telemetry_data.service_id} not found")
            raise
        
        # Create telemetry record
        telemetry = TelemetryRecord(
            service_id=telemetry_data.service_id,
            timestamp=telemetry_data.timestamp,
            cpu_usage_percent=telemetry_data.cpu_usage_percent,
            memory_usage_percent=telemetry_data.memory_usage_percent,
            request_rate=telemetry_data.request_rate,
            error_rate_percent=telemetry_data.error_rate_percent,
            p95_latency_ms=telemetry_data.p95_latency_ms,
            source=telemetry_data.source,
            labels=telemetry_data.labels or {}
        )
        
        try:
            self.db.add(telemetry)
            self.db.commit()
            self.db.refresh(telemetry)
            
            logger.info(f"Telemetry record {telemetry.id} created successfully")
            return telemetry
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to persist telemetry: {e}")
            raise InvalidTelemetryException(str(e))
    
    def get_telemetry_by_id(self, telemetry_id: int) -> Optional[TelemetryRecord]:
        """
        Get telemetry record by ID.
        
        Args:
            telemetry_id: Telemetry record ID
            
        Returns:
            Optional[TelemetryRecord]: Telemetry record or None
        """
        return self.db.query(TelemetryRecord).filter(
            TelemetryRecord.id == telemetry_id
        ).first()
    
    def query_telemetry(
        self,
        service_id: UUID,
        params: TelemetryQueryParams
    ) -> List[TelemetryRecord]:
        """
        Query telemetry records for a service.
        
        Supports time-range filtering and pagination.
        
        Args:
            service_id: Service UUID
            params: Query parameters
            
        Returns:
            List[TelemetryRecord]: List of telemetry records
            
        Raises:
            ServiceNotFoundException: If service doesn't exist
        """
        # Validate service exists
        self.service_manager.get_service_by_id(service_id)
        
        # Build query
        query = self.db.query(TelemetryRecord).filter(
            TelemetryRecord.service_id == service_id
        )
        
        # Apply time filters
        if params.start_time:
            query = query.filter(TelemetryRecord.timestamp >= params.start_time)
        
        if params.end_time:
            query = query.filter(TelemetryRecord.timestamp <= params.end_time)
        
        # Order by timestamp (most recent first)
        query = query.order_by(desc(TelemetryRecord.timestamp))
        
        # Apply pagination
        telemetry_records = query.offset(params.offset).limit(params.limit).all()
        
        logger.info(
            f"Retrieved {len(telemetry_records)} telemetry records for service {service_id}"
        )
        return telemetry_records
    
    def get_latest_telemetry(
        self,
        service_id: UUID,
        count: int = 10
    ) -> List[TelemetryRecord]:
        """
        Get the most recent telemetry records for a service.
        
        Args:
            service_id: Service UUID
            count: Number of records to retrieve
            
        Returns:
            List[TelemetryRecord]: Latest telemetry records
        """
        return self.db.query(TelemetryRecord).filter(
            TelemetryRecord.service_id == service_id
        ).order_by(desc(TelemetryRecord.timestamp)).limit(count).all()
    
    def count_telemetry(
        self,
        service_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """
        Count telemetry records for a service.
        
        Args:
            service_id: Service UUID
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            int: Number of telemetry records
        """
        query = self.db.query(TelemetryRecord).filter(
            TelemetryRecord.service_id == service_id
        )
        
        if start_time:
            query = query.filter(TelemetryRecord.timestamp >= start_time)
        
        if end_time:
            query = query.filter(TelemetryRecord.timestamp <= end_time)
        
        return query.count()
    
    def delete_old_telemetry(
        self,
        service_id: UUID,
        before_timestamp: datetime
    ) -> int:
        """
        Delete telemetry records older than specified timestamp.
        
        Useful for implementing data retention policies.
        
        Args:
            service_id: Service UUID
            before_timestamp: Delete records before this timestamp
            
        Returns:
            int: Number of records deleted
        """
        count = self.db.query(TelemetryRecord).filter(
            TelemetryRecord.service_id == service_id,
            TelemetryRecord.timestamp < before_timestamp
        ).delete()
        
        self.db.commit()
        
        logger.info(f"Deleted {count} old telemetry records for service {service_id}")
        return count
