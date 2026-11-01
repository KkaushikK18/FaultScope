"""
Telemetry ingestion and query API routes.

Provides REST endpoints for ingesting telemetry and querying historical data.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.schemas.telemetry import (
    TelemetryRecordCreate,
    TelemetryRecordResponse,
    TelemetryQueryParams
)
from app.services.telemetry_service import TelemetryService
from app.api.dependencies import get_database_session
from app.core.exceptions import (
    ServiceNotFoundException,
    InvalidTelemetryException
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/telemetry",
    tags=["telemetry"]
)


@router.post(
    "/",
    response_model=TelemetryRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest telemetry",
    description="Ingest a normalized telemetry record for a service"
)
def ingest_telemetry(
    telemetry: TelemetryRecordCreate,
    db: Session = Depends(get_database_session)
):
    """
    Ingest a telemetry record.
    
    **Required fields:**
    - service_id: UUID of the service
    - timestamp: Timezone-aware timestamp
    - cpu_usage_percent: [0-100]
    - memory_usage_percent: [0-100]
    - request_rate: >= 0
    - error_rate_percent: [0-100]
    - p95_latency_ms: >= 0
    
    **Optional fields:**
    - source: Telemetry source (defaults to "api")
    - labels: Additional labels/tags
    
    Returns the created telemetry record with assigned ID.
    """
    try:
        service = TelemetryService(db)
        telemetry_record = service.ingest_telemetry(telemetry)
        return telemetry_record
        
    except ServiceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidTelemetryException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error ingesting telemetry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest telemetry"
        )


@router.get(
    "/{service_id}",
    response_model=List[TelemetryRecordResponse],
    summary="Query telemetry",
    description="Query telemetry records for a service with time-range filtering"
)
def query_telemetry(
    service_id: UUID,
    start_time: str = Query(None, description="Start time (ISO 8601 format)"),
    end_time: str = Query(None, description="End time (ISO 8601 format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_database_session)
):
    """
    Query telemetry records for a service.
    
    Supports:
    - Time-range filtering (start_time, end_time)
    - Pagination (limit, offset)
    
    Results are ordered by timestamp (most recent first).
    """
    try:
        from datetime import datetime
        
        # Parse time parameters
        parsed_start = None
        parsed_end = None
        
        if start_time:
            try:
                parsed_start = datetime.fromisoformat(start_time)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_time format. Use ISO 8601 format."
                )
        
        if end_time:
            try:
                parsed_end = datetime.fromisoformat(end_time)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_time format. Use ISO 8601 format."
                )
        
        # Create query params
        params = TelemetryQueryParams(
            start_time=parsed_start,
            end_time=parsed_end,
            limit=limit,
            offset=offset
        )
        
        service = TelemetryService(db)
        telemetry_records = service.query_telemetry(service_id, params)
        return telemetry_records
        
    except ServiceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying telemetry for service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query telemetry"
        )


@router.get(
    "/{service_id}/latest",
    response_model=List[TelemetryRecordResponse],
    summary="Get latest telemetry",
    description="Get the most recent telemetry records for a service"
)
def get_latest_telemetry(
    service_id: UUID,
    count: int = Query(10, ge=1, le=100, description="Number of records to retrieve"),
    db: Session = Depends(get_database_session)
):
    """
    Get the most recent telemetry records.
    
    Returns the latest N telemetry records ordered by timestamp (most recent first).
    Useful for dashboards and real-time monitoring.
    """
    try:
        service = TelemetryService(db)
        telemetry_records = service.get_latest_telemetry(service_id, count)
        return telemetry_records
        
    except ServiceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving latest telemetry for service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve latest telemetry"
        )


@router.get(
    "/{service_id}/count",
    summary="Count telemetry records",
    description="Get the total count of telemetry records for a service"
)
def count_telemetry(
    service_id: UUID,
    start_time: str = Query(None, description="Start time (ISO 8601 format)"),
    end_time: str = Query(None, description="End time (ISO 8601 format)"),
    db: Session = Depends(get_database_session)
):
    """
    Count telemetry records for a service.
    
    Optionally filter by time range.
    """
    try:
        from datetime import datetime
        
        # Parse time parameters
        parsed_start = None
        parsed_end = None
        
        if start_time:
            try:
                parsed_start = datetime.fromisoformat(start_time)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_time format. Use ISO 8601 format."
                )
        
        if end_time:
            try:
                parsed_end = datetime.fromisoformat(end_time)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_time format. Use ISO 8601 format."
                )
        
        service = TelemetryService(db)
        count = service.count_telemetry(
            service_id,
            start_time=parsed_start,
            end_time=parsed_end
        )
        
        return {
            "service_id": service_id,
            "count": count,
            "start_time": start_time,
            "end_time": end_time
        }
        
    except ServiceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error counting telemetry for service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to count telemetry"
        )
