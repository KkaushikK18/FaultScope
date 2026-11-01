"""
Anomaly detection API routes.

Provides REST endpoints for querying anomaly detection results
and detector information.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.schemas.anomaly import AnomalyResultResponse, AnomalyQueryParams
from app.services.anomaly_service import AnomalyService
from app.api.dependencies import get_database_session
from app.core.exceptions import ServiceNotFoundException
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/anomalies",
    tags=["anomalies"]
)


@router.get(
    "/{service_id}",
    response_model=List[AnomalyResultResponse],
    summary="Query anomalies",
    description="Query anomaly detection results for a service"
)
def query_anomalies(
    service_id: UUID,
    start_time: str = Query(None, description="Start time (ISO 8601)"),
    end_time: str = Query(None, description="End time (ISO 8601)"),
    anomalies_only: bool = Query(True, description="Return only detected anomalies"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records"),
    offset: int = Query(0, ge=0, description="Records to skip"),
    db: Session = Depends(get_database_session)
):
    """
    Query anomaly detection results.
    
    Returns historical anomaly detection results with optional time-range filtering.
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
                    detail="Invalid start_time format"
                )
        
        if end_time:
            try:
                parsed_end = datetime.fromisoformat(end_time)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_time format"
                )
        
        # Create query params
        params = AnomalyQueryParams(
            start_time=parsed_start,
            end_time=parsed_end,
            anomalies_only=anomalies_only,
            limit=limit,
            offset=offset
        )
        
        service = AnomalyService(db)
        results = service.query_anomalies(service_id, params)
        return results
        
    except ServiceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying anomalies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query anomalies"
        )


@router.get(
    "/{service_id}/count",
    summary="Count anomalies",
    description="Get count of anomaly results for a service"
)
def count_anomalies(
    service_id: UUID,
    start_time: str = Query(None, description="Start time (ISO 8601)"),
    end_time: str = Query(None, description="End time (ISO 8601)"),
    anomalies_only: bool = Query(True, description="Count only detected anomalies"),
    db: Session = Depends(get_database_session)
):
    """
    Count anomaly results.
    
    Returns the count of anomaly detection results with optional filtering.
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
                    detail="Invalid start_time format"
                )
        
        if end_time:
            try:
                parsed_end = datetime.fromisoformat(end_time)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_time format"
                )
        
        service = AnomalyService(db)
        count = service.count_anomalies(
            service_id,
            start_time=parsed_start,
            end_time=parsed_end,
            anomalies_only=anomalies_only
        )
        
        return {
            "service_id": service_id,
            "count": count,
            "start_time": start_time,
            "end_time": end_time,
            "anomalies_only": anomalies_only
        }
        
    except ServiceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error counting anomalies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to count anomalies"
        )


@router.get(
    "/detectors/info",
    summary="Get detector information",
    description="Get information about available anomaly detectors"
)
def get_detector_info(db: Session = Depends(get_database_session)):
    """
    Get detector information.
    
    Returns information about available detectors including:
    - Rule-based detector status and thresholds
    - ML detector status and model info
    """
    try:
        service = AnomalyService(db)
        info = service.get_detector_info()
        return info
        
    except Exception as e:
        logger.error(f"Error getting detector info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get detector information"
        )


@router.post(
    "/detectors/reload",
    summary="Reload ML detector",
    description="Reload the ML model from disk (useful after training)"
)
def reload_ml_detector(db: Session = Depends(get_database_session)):
    """
    Reload ML detector.
    
    Attempts to load the latest trained ML model from disk.
    Useful after training a new model.
    """
    try:
        service = AnomalyService(db)
        success = service.reload_ml_model()
        
        if success:
            return {
                "status": "success",
                "message": "ML detector reloaded successfully",
                "detector_info": service.get_detector_info()
            }
        else:
            return {
                "status": "failed",
                "message": "Failed to reload ML detector - no trained model found"
            }
        
    except Exception as e:
        logger.error(f"Error reloading ML detector: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload ML detector"
        )
