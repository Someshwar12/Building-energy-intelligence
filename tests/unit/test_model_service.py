from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.model_service.app.inference import InferenceService
from apps.model_service.app.main import app
from apps.model_service.app.model_loader import ModelLoader
from apps.model_service.app.schemas import PredictionRequest


class FakeModel:
    def predict(self, frame):
        return [123.45]


class FakeLoader:
    model = FakeModel()
    model_name = "test_model"
    model_version = "phase1"
    feature_columns: tuple[str, ...] = (
        "building_id",
        "site_id",
        "primary_use",
        "square_feet",
        "floor_area",
        "timezone",
        "air_temperature",
        "dew_temperature",
        "cloud_coverage",
        "wind_speed",
        "wind_direction",
        "sea_level_pressure",
        "precip_depth_1_hr",
        "hour",
        "day_of_week",
        "month",
        "day_of_year",
        "is_weekend",
        "hour_sin",
        "hour_cos",
        "day_of_year_sin",
        "day_of_year_cos",
        "energy_lag_1h",
        "energy_lag_2h",
        "energy_lag_3h",
        "energy_lag_24h",
        "energy_lag_48h",
        "energy_lag_72h",
        "energy_lag_168h",
        "energy_roll_mean_3h",
        "energy_roll_mean_6h",
        "energy_roll_mean_24h",
        "energy_roll_max_24h",
        "energy_roll_mean_168h",
        "energy_roll_max_168h",
        "heating_degree_hour",
        "cooling_degree_hour",
    )


def make_history(timestamp):
    return [
        {
            "timestamp": timestamp - timedelta(hours=hours),
            "energy_kwh": float(100 + hours),
        }
        for hours in range(168, 0, -1)
    ]


def make_request():
    timestamp = datetime(2017, 1, 8, 12, 0, tzinfo=UTC)

    return PredictionRequest(
        building_id="Bear_assembly_Angel",
        timestamp=timestamp,
        site_id="site_0",
        primary_use="Education",
        square_feet=10000,
        floor_area=929.0,
        timezone="UTC",
        air_temperature=15.2,
        dew_temperature=8.4,
        cloud_coverage=4,
        wind_speed=3.2,
        wind_direction=180,
        sea_level_pressure=1012,
        precip_depth_1_hr=0,
        history=make_history(timestamp),
    )


def test_inference_returns_prediction():
    service = InferenceService(FakeLoader())

    response = service.predict(make_request())

    assert response.predicted_energy_kwh == 123.45
    assert response.model_name == "test_model"
    assert response.model_version == "phase1"


def test_history_requires_168_observations():
    timestamp = datetime(2017, 1, 8, 12, 0, tzinfo=UTC)

    with pytest.raises(ValueError):
        PredictionRequest(
            building_id="Bear_assembly_Angel",
            timestamp=timestamp,
            site_id="site_0",
            primary_use="Education",
            square_feet=10000,
            floor_area=929,
            timezone="UTC",
            history=make_history(timestamp)[:-1],
        )


def test_history_rejects_duplicate_timestamps():
    timestamp = datetime(2017, 1, 8, 12, 0, tzinfo=UTC)
    history = make_history(timestamp)
    history[-1]["timestamp"] = history[-2]["timestamp"]

    with pytest.raises(ValueError, match="duplicate timestamps"):
        PredictionRequest(
            building_id="Bear_assembly_Angel",
            timestamp=timestamp,
            site_id="site_0",
            primary_use="Education",
            square_feet=10000,
            floor_area=929,
            timezone="UTC",
            history=history,
        )


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_endpoint():
    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ready"
    assert body["model_name"] == "random_forest"
    assert body["model_version"] == "phase1"


def test_predict_endpoint_with_real_model():
    timestamp = datetime(2017, 1, 8, 12, 0, tzinfo=UTC)

    payload = {
        "building_id": "Bear_assembly_Angel",
        "timestamp": timestamp.isoformat(),
        "site_id": "site_0",
        "primary_use": "Education",
        "square_feet": 10000,
        "floor_area": 929.0,
        "timezone": "UTC",
        "air_temperature": 15.2,
        "dew_temperature": 8.4,
        "cloud_coverage": 4,
        "wind_speed": 3.2,
        "wind_direction": 180,
        "sea_level_pressure": 1012,
        "precip_depth_1_hr": 0,
        "history": [
            {
                "timestamp": (
                    timestamp - timedelta(hours=hours)
                ).isoformat(),
                "energy_kwh": float(100 + hours),
            }
            for hours in range(168, 0, -1)
        ],
    }

    with TestClient(app) as client:
        response = client.post("/predict", json=payload)

    assert response.status_code == 200

    body = response.json()

    assert body["building_id"] == "Bear_assembly_Angel"
    assert body["model_name"] == "random_forest"
    assert body["model_version"] == "phase1"
    assert isinstance(body["predicted_energy_kwh"], float)
    assert body["predicted_energy_kwh"] >= 0


def test_predict_rejects_incomplete_history():
    timestamp = datetime(2017, 1, 8, 12, 0, tzinfo=UTC)

    payload = {
        "building_id": "Bear_assembly_Angel",
        "timestamp": timestamp.isoformat(),
        "site_id": "site_0",
        "primary_use": "Education",
        "square_feet": 10000,
        "floor_area": 929.0,
        "timezone": "UTC",
        "history": [
            {
                "timestamp": (
                    timestamp - timedelta(hours=hours)
                ).isoformat(),
                "energy_kwh": float(100 + hours),
            }
            for hours in range(168, 1, -1)
        ],
    }

    with TestClient(app) as client:
        response = client.post("/predict", json=payload)

    assert response.status_code == 422


def test_predict_rejects_non_consecutive_history():
    timestamp = datetime(2017, 1, 8, 12, 0, tzinfo=UTC)

    history = make_history(timestamp)

    history = [
        {
            "timestamp": item["timestamp"].isoformat(),
            "energy_kwh": item["energy_kwh"],
        }
        for item in history
    ]

    history[10]["timestamp"] = (
        datetime.fromisoformat(history[10]["timestamp"])
        - timedelta(hours=1)
    ).isoformat()

    payload = {
        "building_id": "Bear_assembly_Angel",
        "timestamp": timestamp.isoformat(),
        "site_id": "site_0",
        "primary_use": "Education",
        "square_feet": 10000,
        "floor_area": 929.0,
        "timezone": "UTC",
        "history": history,
    }

    with TestClient(app) as client:
        response = client.post("/predict", json=payload)

    assert response.status_code == 422

def test_model_loader_rejects_missing_artifact(tmp_path: Path):
    loader = ModelLoader(
        tmp_path / "missing_model.joblib"
    )

    with pytest.raises(
        FileNotFoundError,
        match="Model artifact not found",
    ):
        loader.initialize()


def test_model_loader_rejects_invalid_artifact(tmp_path: Path):
    artifact_path = tmp_path / "invalid_model.joblib"

    artifact_path.write_bytes(b"not a valid joblib artifact")

    loader = ModelLoader(artifact_path)

    with pytest.raises(
        ValueError,
        match="Unable to load model artifact",
    ):
        loader.initialize()


def test_predict_rejects_negative_energy_history():
    timestamp = datetime(
        2017,
        1,
        8,
        12,
        0,
        tzinfo=UTC,
    )

    payload = {
        "building_id": "Bear_assembly_Angel",
        "timestamp": timestamp.isoformat(),
        "site_id": "site_0",
        "primary_use": "Education",
        "square_feet": 10000,
        "floor_area": 929.0,
        "timezone": "UTC",
        "history": [
            {
                "timestamp": (
                    timestamp - timedelta(hours=hours)
                ).isoformat(),
                "energy_kwh": -1.0,
            }
            for hours in range(168, 0, -1)
        ],
    }

    with TestClient(app) as client:
        response = client.post("/predict", json=payload)

    assert response.status_code == 422


def test_predict_rejects_invalid_building_metadata():
    timestamp = datetime(
        2017,
        1,
        8,
        12,
        0,
        tzinfo=UTC,
    )

    payload = {
        "building_id": "",
        "timestamp": timestamp.isoformat(),
        "site_id": "site_0",
        "primary_use": "Education",
        "square_feet": 10000,
        "floor_area": 929.0,
        "timezone": "UTC",
        "history": [
            {
                "timestamp": (
                    timestamp - timedelta(hours=hours)
                ).isoformat(),
                "energy_kwh": float(100 + hours),
            }
            for hours in range(168, 0, -1)
        ],
    }

    with TestClient(app) as client:
        response = client.post("/predict", json=payload)

    assert response.status_code == 422