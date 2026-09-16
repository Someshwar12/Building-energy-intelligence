import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SERVICE_NAME = "building-energy-model-service"
SERVICE_VERSION = "0.1.0"

MODEL_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODEL_DIR / "random_forest_phase1.joblib"

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)

MLFLOW_MODEL_NAME = os.getenv(
    "MLFLOW_MODEL_NAME",
    "building-energy-forecast",
)

MLFLOW_MODEL_ALIAS = os.getenv(
    "MLFLOW_MODEL_ALIAS",
    "production",
)

MODEL_SOURCE = os.getenv(
    "MODEL_SOURCE",
    "local",
)