from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SERVICE_NAME = "building-energy-model-service"
SERVICE_VERSION = "0.1.0"

MODEL_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODEL_DIR / "random_forest_phase1.joblib"