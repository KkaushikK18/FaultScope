"""
Pydantic schemas for Service entities.

These schemas define the API contract for service management endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ServiceStatus(str, Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class ServiceBase(BaseModel):
    """Base service attributes shared across schemas"""
    service_name: str = Field(..., min_length=1, max_length=255, description="Unique service name")
    environment: str = Field(..., min_length=1, max_length=50, description="Deployment environment")
    meta: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional service metadata")


class ServiceCreate(ServiceBase):
    """Schema for creating a new service"""
    status: ServiceStatus = Field(default=ServiceStatus.HEALTHY, description="Initial service status")


class ServiceUpdate(BaseModel):
    """Schema for updating an existing service"""
    status: Optional[ServiceStatus] = Field(default=None, description="Updated service status")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Updated metadata")


class ServiceResponse(ServiceBase):
    """Schema for service API responses"""
    id: UUID = Field(..., description="Unique service identifier")
    status: ServiceStatus = Field(..., description="Current service status")
    created_at: datetime = Field(..., description="Service registration timestamp")
    
    model_config = ConfigDict(from_attributes=True)
