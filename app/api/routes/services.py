"""
Service management API routes.

Provides REST endpoints for creating, reading, updating, and deleting services.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.services.service_manager import ServiceManager
from app.api.dependencies import get_database_session
from app.core.exceptions import (
    ServiceNotFoundException,
    ServiceAlreadyExistsException
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/services",
    tags=["services"]
)


@router.post(
    "/",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new service",
    description="Register a new service to be monitored by FaultScope"
)
def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_database_session)
):
    """
    Register a new service.
    
    - **service_name**: Unique name for the service
    - **environment**: Deployment environment (e.g., production, staging, local)
    - **status**: Initial health status (defaults to healthy)
    - **meta**: Optional metadata dictionary
    
    Returns the created service with assigned UUID.
    """
    try:
        manager = ServiceManager(db)
        created_service = manager.create_service(service)
        return created_service
        
    except ServiceAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create service"
        )


@router.get(
    "/",
    response_model=List[ServiceResponse],
    summary="List all services",
    description="Retrieve a list of all registered services with optional filtering"
)
def list_services(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    db: Session = Depends(get_database_session)
):
    """
    List all registered services.
    
    Supports pagination and filtering by environment.
    """
    try:
        manager = ServiceManager(db)
        services = manager.list_services(
            skip=skip,
            limit=limit,
            environment=environment
        )
        return services
        
    except Exception as e:
        logger.error(f"Error listing services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve services"
        )


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Get service by ID",
    description="Retrieve details of a specific service"
)
def get_service(
    service_id: UUID,
    db: Session = Depends(get_database_session)
):
    """
    Get service details by ID.
    
    Returns service information including status, metadata, and registration timestamp.
    """
    try:
        manager = ServiceManager(db)
        service = manager.get_service_by_id(service_id)
        return service
        
    except ServiceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service"
        )


@router.patch(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Update service",
    description="Update service status or metadata"
)
def update_service(
    service_id: UUID,
    service_update: ServiceUpdate,
    db: Session = Depends(get_database_session)
):
    """
    Update an existing service.
    
    Can update:
    - **status**: Service health status
    - **meta**: Service metadata
    
    Only provided fields will be updated.
    """
    try:
        manager = ServiceManager(db)
        updated_service = manager.update_service(service_id, service_update)
        return updated_service
        
    except ServiceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update service"
        )


@router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete service",
    description="Delete a service and all associated data (telemetry, anomalies, incidents)"
)
def delete_service(
    service_id: UUID,
    db: Session = Depends(get_database_session)
):
    """
    Delete a service.
    
    **WARNING**: This will cascade delete all related data:
    - Telemetry records
    - Anomaly results
    - Incidents
    
    This action cannot be undone.
    """
    try:
        manager = ServiceManager(db)
        manager.delete_service(service_id)
        return None
        
    except ServiceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete service"
        )


@router.get(
    "/{service_id}/stats",
    summary="Get service statistics",
    description="Get statistics for a service including telemetry count"
)
def get_service_stats(
    service_id: UUID,
    db: Session = Depends(get_database_session)
):
    """
    Get statistics for a service.
    
    Returns:
    - Total telemetry records count
    - Service details
    """
    try:
        from app.services.telemetry_service import TelemetryService
        
        manager = ServiceManager(db)
        telemetry_service = TelemetryService(db)
        
        # Get service
        service = manager.get_service_by_id(service_id)
        
        # Get telemetry count
        telemetry_count = telemetry_service.count_telemetry(service_id)
        
        return {
            "service_id": service_id,
            "service_name": service.service_name,
            "environment": service.environment,
            "status": service.status,
            "telemetry_count": telemetry_count,
            "created_at": service.created_at
        }
        
    except ServiceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving service stats {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service statistics"
        )
