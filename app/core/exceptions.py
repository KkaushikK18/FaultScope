"""
Custom exceptions for FaultScope.

Provides domain-specific exceptions for better error handling and reporting.
"""


class FaultScopeException(Exception):
    """Base exception for all FaultScope errors"""
    pass


class ServiceNotFoundException(FaultScopeException):
    """Raised when a service is not found in the database"""
    
    def __init__(self, service_id: str):
        self.service_id = service_id
        super().__init__(f"Service not found: {service_id}")


class ServiceAlreadyExistsException(FaultScopeException):
    """Raised when attempting to create a service that already exists"""
    
    def __init__(self, service_name: str, environment: str):
        self.service_name = service_name
        self.environment = environment
        super().__init__(
            f"Service already exists: {service_name} in environment {environment}"
        )


class InvalidTelemetryException(FaultScopeException):
    """Raised when telemetry data fails validation"""
    
    def __init__(self, message: str):
        super().__init__(f"Invalid telemetry: {message}")


class ModelNotFoundException(FaultScopeException):
    """Raised when a required ML model is not found"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        super().__init__(f"Model not found: {model_name}")


class InsufficientTrainingDataException(FaultScopeException):
    """Raised when there is insufficient data to train a model"""
    
    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient training data: required {required}, available {available}"
        )


class IncidentNotFoundException(FaultScopeException):
    """Raised when an incident is not found in the database"""
    
    def __init__(self, incident_id: str):
        self.incident_id = incident_id
        super().__init__(f"Incident not found: {incident_id}")


class DatabaseException(FaultScopeException):
    """Raised when a database operation fails"""
    
    def __init__(self, message: str):
        super().__init__(f"Database error: {message}")
