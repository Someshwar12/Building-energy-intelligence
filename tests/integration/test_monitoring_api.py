from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

import apps.model_service.app.main as main_module
from apps.model_service.app.inference import InferenceService


class FakeModel:
    def predict(self, features):
        return [123.45]

class FakeLoader:
    model_name = "test_model"
    model_version = "phase5-monitoring"
    serving_mode = "learned"

    feature_columns = (
        "building_id",
        "site_id",
        "primary_use",
        "square_feet",
        "floor_area",
        "air_temperature",
        "dew_temperature",
        "sea_level_pressure",
        "wind_direction",
        "wind_speed",
        "cloud_coverage",
        "precip_depth_1_hr",
        "hour",
        "day_of_week",
        "day_of_month",
        "month",
        "week_of_year",
        "is_weekend",
        "lag_1",
        "lag_24",
        "lag_168",
        "rolling_mean_24",
        "rolling_std_24",
        "rolling_mean_168",
        "rolling_std_168",
        "heating_degree_hours",
        "cooling_degree_hours",
    )

    model = FakeModel()

    def initialize(self):
        return None

    @property
    def is_ready(self):
        return True


def make_client(monkeypatch):
    loader = FakeLoader()

    monkeypatch.setattr(main_module, "model_loader", loader)
    monkeypatch.setattr(
        main_module,
        "inference_service",
        InferenceService(loader),
    )

    main_module.monitoring_state = main_module.MonitoringState()

    return TestClient(main_module.app)


def make_payload():
    start = datetime(
        2017,
        12,
        24,
        tzinfo=UTC,
    )

    history = [
        {
            "timestamp": (
                start + timedelta(hours=index)
            ).isoformat(),
            "energy_kwh": 100.0 + index,
        }
        for index in range(168)
    ]

    return {
        "building_id": "test_building",
        "site_id": "test_site",
        "primary_use": "Office",
        "square_feet": 10000.0,
        "floor_area": 10000.0,
        "timezone": "UTC",
        "timestamp": (
            start + timedelta(hours=168)
        ).isoformat(),
        "air_temperature": 10.0,
        "dew_temperature": 5.0,
        "sea_level_pressure": 1015.0,
        "wind_direction": 180.0,
        "wind_speed": 3.0,
        "cloud_coverage": 2.0,
        "precip_depth_1_hr": 0.0,
        "history": history,
    }


def test_monitoring_summary_starts_empty(monkeypatch):
    with make_client(monkeypatch) as client:
        response = client.get("/monitoring/summary")

    assert response.status_code == 200

    body = response.json()

    assert body["service"]["status"] == "ready"
    assert body["service"]["model_name"] == "test_model"
    assert body["service"]["model_version"] == "phase5-monitoring"
    assert body["monitoring"]["requests"]["total"] == 0


def test_prediction_updates_monitoring_summary(monkeypatch):
    with make_client(monkeypatch) as client:
        prediction = client.post(
            "/predict",
            json=make_payload(),
        )

        assert prediction.status_code == 200

        response = client.get("/monitoring/summary")

    assert response.status_code == 200

    body = response.json()

    assert body["monitoring"]["requests"]["total"] == 1
    assert body["monitoring"]["requests"]["successful"] == 1
    assert body["monitoring"]["requests"]["failed"] == 0
    assert body["monitoring"]["latency_ms"]["sample_count"] == 1
    assert body["monitoring"]["serving_modes"]["learned"] == 1
    assert body["monitoring"]["data_quality"]["healthy"] == 1