"""
Setup verification script.

Verifies that the FaultScope environment is properly configured.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def verify_imports():
    """Verify all core imports work"""
    print("🔍 Verifying imports...")
    try:
        from app.core.config import get_settings
        from app.core.logging import setup_logging
        from app.core.exceptions import FaultScopeException
        from app.schemas import (
            ServiceCreate, TelemetryRecordCreate,
            AnomalyResultCreate, IncidentCreate
        )
        from app.database.models import Service, TelemetryRecord, AnomalyResult, Incident
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def verify_config():
    """Verify configuration loads correctly"""
    print("\n🔍 Verifying configuration...")
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        print(f"  App Name: {settings.APP_NAME}")
        print(f"  Version: {settings.APP_VERSION}")
        print(f"  Database URL: {settings.DATABASE_URL[:50]}...")
        print(f"  Min Training Samples: {settings.MIN_TRAINING_SAMPLES}")
        print(f"  Rule CPU Threshold: {settings.RULE_CPU_THRESHOLD}")
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False


def verify_schemas():
    """Verify Pydantic schemas work correctly"""
    print("\n🔍 Verifying Pydantic schemas...")
    try:
        from app.schemas import ServiceCreate, ServiceStatus
        from datetime import datetime, timezone
        import uuid
        
        # Test service schema
        service = ServiceCreate(
            service_name="test-service",
            environment="local",
            status=ServiceStatus.HEALTHY
        )
        assert service.service_name == "test-service"
        
        # Test telemetry schema with validation
        from app.schemas import TelemetryRecordCreate
        telemetry = TelemetryRecordCreate(
            service_id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            cpu_usage_percent=50.0,
            memory_usage_percent=60.0,
            request_rate=100.0,
            error_rate_percent=2.5,
            p95_latency_ms=150.0
        )
        assert telemetry.cpu_usage_percent == 50.0
        
        # Test invalid telemetry (should raise validation error)
        try:
            invalid = TelemetryRecordCreate(
                service_id=uuid.uuid4(),
                timestamp=datetime.now(timezone.utc),
                cpu_usage_percent=150.0,  # Invalid: > 100
                memory_usage_percent=60.0,
                request_rate=100.0,
                error_rate_percent=2.5,
                p95_latency_ms=150.0
            )
            print("❌ Validation should have failed for invalid CPU usage")
            return False
        except Exception:
            pass  # Expected to fail
        
        print("✅ Schemas validated successfully")
        return True
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False


def verify_database_models():
    """Verify database models are defined correctly"""
    print("\n🔍 Verifying database models...")
    try:
        from app.database.models import Service, TelemetryRecord, AnomalyResult, Incident
        from app.database.base import Base
        
        # Check that models have proper table names
        assert Service.__tablename__ == "services"
        assert TelemetryRecord.__tablename__ == "telemetry_records"
        assert AnomalyResult.__tablename__ == "anomaly_results"
        assert Incident.__tablename__ == "incidents"
        
        # Check that models are registered with Base
        tables = Base.metadata.tables
        assert "services" in tables
        assert "telemetry_records" in tables
        assert "anomaly_results" in tables
        assert "incidents" in tables
        
        print("✅ Database models verified successfully")
        return True
    except Exception as e:
        print(f"❌ Database model verification failed: {e}")
        return False


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("FaultScope v0.1 - Setup Verification")
    print("=" * 60)
    
    checks = [
        verify_imports,
        verify_config,
        verify_schemas,
        verify_database_models,
    ]
    
    results = [check() for check in checks]
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ All verification checks passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start Docker Compose: docker-compose up -d")
        print("2. Check API health: curl http://localhost:8000/health")
        print("3. View API docs: http://localhost:8000/docs")
        return 0
    else:
        print("❌ Some verification checks failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
