"""
Service Manager - Business logic for service management.

Handles CRUD operations for monitored services with proper error handling
and validation.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate
from app.core.exceptions import ServiceNotFoundException, ServiceAlreadyExistsException
from app.core.logging import get_logger

logger = get_logger(__name__)


class ServiceManager:
    """
    Manager class for service operations.
    
    Encapsulates all business logic related to service management.
    """
    
    def __init__(self, db: Session):
        """
        Initialize service manager.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_service(self, service_data: ServiceCreate) -> Service:
        """
        Create a new service.
        
        Args:
            service_data: Service creation data
            
        Returns:
            Service: Created service instance
            
        Raises:
            ServiceAlreadyExistsException: If service already exists
        """
        logger.info(f"Creating service: {service_data.service_name} in {service_data.environment}")
        
        # Create service instance
        service = Service(
            service_name=service_data.service_name,
            environment=service_data.environment,
            status=service_data.status.value,
            meta=service_data.meta or {}
        )
        
        try:
            self.db.add(service)
            self.db.commit()
            self.db.refresh(service)
            
            logger.info(f"Service created successfully: {service.id}")
            return service
            
        except IntegrityError as e:
            self.db.rollback()
            logger.warning(f"Service already exists: {service_data.service_name} in {service_data.environment}")
            raise ServiceAlreadyExistsException(
                service_data.service_name,
                service_data.environment
            )
    
    def get_service_by_id(self, service_id: UUID) -> Service:
        """
        Get service by ID.
        
        Args:
            service_id: Service UUID
            
        Returns:
            Service: Service instance
            
        Raises:
            ServiceNotFoundException: If service not found
        """
        service = self.db.query(Service).filter(Service.id == service_id).first()
        
        if not service:
            logger.warning(f"Service not found: {service_id}")
            raise ServiceNotFoundException(str(service_id))
        
        return service
    
    def get_service_by_name_and_env(
        self,
        service_name: str,
        environment: str
    ) -> Optional[Service]:
        """
        Get service by name and environment.
        
        Args:
            service_name: Service name
            environment: Environment name
            
        Returns:
            Optional[Service]: Service instance or None
        """
        return self.db.query(Service).filter(
            Service.service_name == service_name,
            Service.environment == environment
        ).first()
    
    def list_services(
        self,
        skip: int = 0,
        limit: int = 100,
        environment: Optional[str] = None
    ) -> List[Service]:
        """
        List all services with optional filtering.
        
        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            environment: Optional environment filter
            
        Returns:
            List[Service]: List of services
        """
        query = self.db.query(Service)
        
        if environment:
            query = query.filter(Service.environment == environment)
        
        services = query.offset(skip).limit(limit).all()
        
        logger.info(f"Retrieved {len(services)} services")
        return services
    
    def update_service(
        self,
        service_id: UUID,
        service_data: ServiceUpdate
    ) -> Service:
        """
        Update an existing service.
        
        Args:
            service_id: Service UUID
            service_data: Service update data
            
        Returns:
            Service: Updated service instance
            
        Raises:
            ServiceNotFoundException: If service not found
        """
        service = self.get_service_by_id(service_id)
        
        # Update fields if provided
        if service_data.status is not None:
            service.status = service_data.status.value
            logger.info(f"Updated service {service_id} status to {service_data.status.value}")
        
        if service_data.meta is not None:
            service.meta = service_data.meta
            logger.info(f"Updated service {service_id} metadata")
        
        self.db.commit()
        self.db.refresh(service)
        
        return service
    
    def delete_service(self, service_id: UUID) -> None:
        """
        Delete a service.
        
        Note: This will cascade delete all related telemetry, anomalies, and incidents.
        
        Args:
            service_id: Service UUID
            
        Raises:
            ServiceNotFoundException: If service not found
        """
        service = self.get_service_by_id(service_id)
        
        logger.warning(f"Deleting service {service_id} and all related data")
        self.db.delete(service)
        self.db.commit()
        
        logger.info(f"Service {service_id} deleted successfully")
    
    def count_services(self, environment: Optional[str] = None) -> int:
        """
        Count total number of services.
        
        Args:
            environment: Optional environment filter
            
        Returns:
            int: Number of services
        """
        query = self.db.query(Service)
        
        if environment:
            query = query.filter(Service.environment == environment)
        
        return query.count()
