"""
Anomaly Detection Model Training Script.

Trains an Isolation Forest model on historical telemetry data.

Usage:
    python scripts/train_anomaly_model.py --service-id <UUID> --days 7
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    print("Warning: .env file not found. Using environment variables.")
    print(f"Looked for: {env_path}")

from app.database.connection import SessionLocal
from app.services.telemetry_service import TelemetryService
from app.ml.features.feature_extractor import FeatureExtractor
from app.ml.detectors.isolation_forest import IsolationForestDetector
from app.ml.model_loader import ModelLoader
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import InsufficientTrainingDataException
from app.core.config import get_settings

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


def train_model(service_id: str, days: int = 7, contamination: float = None):
    """
    Train Isolation Forest model on historical telemetry.
    
    Args:
        service_id: Service UUID
        days: Number of days of history to use for training
        contamination: Expected anomaly rate (uses config default if None)
    """
    logger.info("=" * 60)
    logger.info("FaultScope - Anomaly Detection Model Training")
    logger.info("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Get training data
        logger.info(f"Fetching telemetry data for service {service_id}")
        logger.info(f"Training window: last {days} days")
        
        from app.database.models.telemetry import TelemetryRecord
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        telemetry_records = db.query(TelemetryRecord).filter(
            TelemetryRecord.service_id == service_id,
            TelemetryRecord.timestamp >= start_time,
            TelemetryRecord.timestamp <= end_time
        ).all()
        
        logger.info(f"Retrieved {len(telemetry_records)} telemetry records")
        
        # Check minimum data requirement
        if len(telemetry_records) < settings.MIN_TRAINING_SAMPLES:
            raise InsufficientTrainingDataException(
                required=settings.MIN_TRAINING_SAMPLES,
                available=len(telemetry_records)
            )
        
        # Extract features
        logger.info("Extracting features...")
        feature_extractor = FeatureExtractor()
        features = feature_extractor.extract_batch(telemetry_records)
        
        logger.info(f"Feature matrix shape: {features.shape}")
        logger.info(f"Features: {feature_extractor.get_feature_names()}")
        
        # Train model
        logger.info("Training Isolation Forest...")
        detector = IsolationForestDetector(contamination=contamination)
        training_stats = detector.train(features)
        
        logger.info("Training statistics:")
        for key, value in training_stats.items():
            logger.info(f"  {key}: {value}")
        
        # Save model
        logger.info("Saving model...")
        model_loader = ModelLoader()
        
        training_metadata = {
            "service_id": service_id,
            "training_days": days,
            "training_window": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "n_training_samples": len(telemetry_records),
            "training_stats": training_stats
        }
        
        model_path = model_loader.save_isolation_forest(detector, training_metadata)
        
        logger.info(f"Model saved to: {model_path}")
        logger.info("=" * 60)
        logger.info("Training complete!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Restart FaultScope API to load the new model")
        logger.info("   OR")
        logger.info("2. Call POST /api/v1/anomalies/detectors/reload")
        logger.info("")
        
        return model_path
        
    except InsufficientTrainingDataException as e:
        logger.error(f"Insufficient training data: {e}")
        logger.error(f"Minimum required: {e.required}, Available: {e.available}")
        logger.error(f"Please collect more telemetry data before training")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Train anomaly detection model on historical telemetry"
    )
    
    parser.add_argument(
        "--service-id",
        type=str,
        required=True,
        help="Service UUID to train model for"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days of history to use (default: 7)"
    )
    
    parser.add_argument(
        "--contamination",
        type=float,
        default=None,
        help=f"Expected anomaly rate 0-0.5 (default: {settings.ISOLATION_FOREST_CONTAMINATION})"
    )
    
    args = parser.parse_args()
    
    # Validate contamination
    if args.contamination is not None:
        if not (0 < args.contamination < 0.5):
            logger.error("Contamination must be between 0 and 0.5")
            sys.exit(1)
    
    # Train model
    train_model(
        service_id=args.service_id,
        days=args.days,
        contamination=args.contamination
    )


if __name__ == "__main__":
    main()
