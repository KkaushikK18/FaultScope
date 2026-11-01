"""
Model Loader - Handles model persistence and loading.

Provides utilities for saving and loading trained ML models and their
associated preprocessing artifacts (scalers, etc.).
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import joblib

from app.ml.detectors.isolation_forest import IsolationForestDetector
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.exceptions import ModelNotFoundException

logger = get_logger(__name__)
settings = get_settings()


class ModelLoader:
    """
    Handles saving and loading of trained models.
    
    Saves models with metadata including:
    - Training timestamp
    - Model parameters
    - Training statistics
    - Preprocessing artifacts
    """
    
    def __init__(self, model_dir: Optional[str] = None):
        """
        Initialize model loader.
        
        Args:
            model_dir: Directory for model storage (uses config default if None)
        """
        self.model_dir = Path(model_dir or settings.MODEL_PATH)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Model directory: {self.model_dir}")
    
    def save_isolation_forest(
        self,
        detector: IsolationForestDetector,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save Isolation Forest detector to disk.
        
        Args:
            detector: Trained IsolationForestDetector
            metadata: Additional metadata to save
        
        Returns:
            str: Path to saved model
        
        Raises:
            ValueError: If detector is not trained
        """
        if not detector.is_trained():
            raise ValueError("Cannot save untrained detector")
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        model_name = f"{detector.name}_{timestamp}"
        model_path = self.model_dir / model_name
        model_path.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_file = model_path / "model.joblib"
        joblib.dump(detector.model, model_file)
        logger.info(f"Saved model to {model_file}")
        
        # Save scaler
        scaler_file = model_path / "scaler.joblib"
        joblib.dump(detector.scaler, scaler_file)
        logger.info(f"Saved scaler to {scaler_file}")
        
        # Save metadata
        model_metadata = {
            "model_name": detector.name,
            "model_type": "isolation_forest",
            "saved_at": datetime.utcnow().isoformat(),
            "parameters": {
                "contamination": detector.contamination,
                "n_estimators": detector.n_estimators,
                "random_state": detector.random_state
            },
            "score_statistics": {
                "score_min": detector.score_min,
                "score_max": detector.score_max
            },
            "model_info": detector.get_model_info()
        }
        
        if metadata:
            model_metadata["training_metadata"] = metadata
        
        metadata_file = model_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(model_metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_file}")
        
        # Create a "latest" symlink (or copy on Windows)
        latest_path = self.model_dir / f"{detector.name}_latest"
        if latest_path.exists():
            if latest_path.is_symlink() or latest_path.is_dir():
                import shutil
                shutil.rmtree(latest_path, ignore_errors=True)
        
        # On Windows, copy instead of symlink
        import shutil
        shutil.copytree(model_path, latest_path, dirs_exist_ok=True)
        logger.info(f"Created latest model link at {latest_path}")
        
        return str(model_path)
    
    def load_isolation_forest(
        self,
        model_name: Optional[str] = None,
        use_latest: bool = True
    ) -> IsolationForestDetector:
        """
        Load Isolation Forest detector from disk.
        
        Args:
            model_name: Specific model name or path (relative to model_dir)
            use_latest: If True and model_name is None, load latest model
        
        Returns:
            IsolationForestDetector: Loaded detector
        
        Raises:
            ModelNotFoundException: If model not found
        """
        # Determine model path
        if model_name:
            model_path = self.model_dir / model_name
        elif use_latest:
            model_path = self.model_dir / "isolation_forest_latest"
        else:
            raise ValueError("Must provide model_name or use_latest=True")
        
        if not model_path.exists():
            raise ModelNotFoundException(str(model_path))
        
        # Load metadata
        metadata_file = model_path / "metadata.json"
        if not metadata_file.exists():
            raise ModelNotFoundException(f"Metadata not found: {metadata_file}")
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        logger.info(f"Loading model from {model_path}")
        
        # Create detector instance
        params = metadata["parameters"]
        detector = IsolationForestDetector(
            name=metadata["model_name"],
            contamination=params["contamination"],
            n_estimators=params["n_estimators"],
            random_state=params["random_state"]
        )
        
        # Load model
        model_file = model_path / "model.joblib"
        if not model_file.exists():
            raise ModelNotFoundException(f"Model file not found: {model_file}")
        
        detector.model = joblib.load(model_file)
        logger.info(f"Loaded model from {model_file}")
        
        # Load scaler
        scaler_file = model_path / "scaler.joblib"
        if not scaler_file.exists():
            raise ModelNotFoundException(f"Scaler file not found: {scaler_file}")
        
        detector.scaler = joblib.load(scaler_file)
        logger.info(f"Loaded scaler from {scaler_file}")
        
        # Restore score statistics
        stats = metadata["score_statistics"]
        detector.score_min = stats["score_min"]
        detector.score_max = stats["score_max"]
        
        logger.info(f"Successfully loaded {detector.name}")
        return detector
    
    def list_models(self) -> list:
        """
        List all saved models.
        
        Returns:
            List of model directories
        """
        models = []
        for path in self.model_dir.iterdir():
            if path.is_dir() and (path / "metadata.json").exists():
                metadata_file = path / "metadata.json"
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                models.append({
                    "path": str(path.name),
                    "model_name": metadata.get("model_name"),
                    "model_type": metadata.get("model_type"),
                    "saved_at": metadata.get("saved_at")
                })
        
        return sorted(models, key=lambda x: x["saved_at"], reverse=True)
    
    def delete_model(self, model_name: str) -> None:
        """
        Delete a saved model.
        
        Args:
            model_name: Model directory name
        """
        model_path = self.model_dir / model_name
        if model_path.exists():
            import shutil
            shutil.rmtree(model_path)
            logger.info(f"Deleted model: {model_path}")
        else:
            logger.warning(f"Model not found: {model_path}")
