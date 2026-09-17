from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apps.model_service.app import main
from apps.model_service.app.inference import InferenceService


class FakeModel:
    def predict(self, features):
        return [123.45]


class FakeLoader:
    feature_columns = (
        "square_feet",
        "floor_area",
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
        "energy_kwh",
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

    model_name = "random_forest"
    model_version = "phase1"
    serving_mode = "local"
    is_ready = True

    def __init__(self):
        self.model = FakeModel()

    def initialize(self):
        return None


def make_payload(
    air_temperature: float = 10.0,
    dew_temperature: float = 5.0,
    energy_kwh: float = 100.0,
) -> dict:
    start = datetime(
        2017,
        12,
        24,
        tzinfo=UTC,
    )

    history = []

    for index in range(168):
        history.append(
            {
                "timestamp": (
                    start
                    + timedelta(hours=index)
                ).isoformat(),
                "energy_kwh": energy_kwh,
            }
        )

    return {
        "building_id": "test_building",
        "site_id": "test_site",
        "primary_use": "Office",
        "square_feet": 10000.0,
        "floor_area": 10000.0,
        "timezone": "UTC",
        "timestamp": (
            start
            + timedelta(hours=168)
        ).isoformat(),
        "air_temperature": air_temperature,
        "dew_temperature": dew_temperature,
        "sea_level_pressure": 1015.0,
        "wind_direction": 180.0,
        "wind_speed": 3.0,
        "cloud_coverage": 2.0,
        "precip_depth_1_hr": 0.0,
        "history": history,
    }


def make_reference_profile() -> dict:
    return {
        "available": True,
        "source": "test-reference",
        "sample_count": 1000,
        "features": {
            "square_feet": {
                "values": [10000.0] * 100,
            },
            "floor_area": {
                "values": [10000.0] * 100,
            },
            "air_temperature": {
                "values": [10.0] * 100,
            },
            "dew_temperature": {
                "values": [5.0] * 100,
            },
            "sea_level_pressure": {
                "values": [1015.0] * 100,
            },
            "wind_direction": {
                "values": [180.0] * 100,
            },
            "wind_speed": {
                "values": [3.0] * 100,
            },
            "cloud_coverage": {
                "values": [2.0] * 100,
            },
            "precip_depth_1_hr": {
                "values": [0.0] * 100,
            },
            "energy_kwh": {
                "values": [100.0] * 100,
            },
            "energy_lag_1h": {
                "values": [100.0] * 100,
            },
            "energy_lag_2h": {
                "values": [100.0] * 100,
            },
            "energy_lag_3h": {
                "values": [100.0] * 100,
            },
            "energy_lag_24h": {
                "values": [100.0] * 100,
            },
            "energy_lag_48h": {
                "values": [100.0] * 100,
            },
            "energy_lag_72h": {
                "values": [100.0] * 100,
            },
            "energy_lag_168h": {
                "values": [100.0] * 100,
            },
            "energy_roll_mean_3h": {
                "values": [100.0] * 100,
            },
            "energy_roll_mean_6h": {
                "values": [100.0] * 100,
            },
            "energy_roll_mean_24h": {
                "values": [100.0] * 100,
            },
            "energy_roll_max_24h": {
                "values": [100.0] * 100,
            },
            "energy_roll_mean_168h": {
                "values": [100.0] * 100,
            },
            "energy_roll_max_168h": {
                "values": [100.0] * 100,
            },
            "heating_degree_hour": {
                "values": [8.0] * 100,
            },
            "cooling_degree_hour": {
                "values": [0.0] * 100,
            },
        },
    }


def make_client(monkeypatch):
    loader = FakeLoader()

    monkeypatch.setattr(
        main,
        "model_loader",
        loader,
    )

    monkeypatch.setattr(
        main,
        "inference_service",
        InferenceService(loader),
    )

    main.monitoring_state = (
        main.MonitoringState()
    )

    monkeypatch.setattr(
        main,
        "load_reference_profile",
        make_reference_profile,
    )

    return TestClient(main.app)


def test_drift_starts_with_insufficient_data(
    monkeypatch,
):
    with make_client(monkeypatch) as client:
        response = client.get(
            "/monitoring/drift"
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == (
        "insufficient_data"
    )
    assert payload["sample_count"] == 0
    assert payload["reference"]["available"] is True


def test_drift_becomes_healthy_after_enough_stable_predictions(
    monkeypatch,
):
    with make_client(monkeypatch) as client:
        for _ in range(30):
            response = client.post(
                "/predict",
                json=make_payload(),
            )

            assert response.status_code == 200

        response = client.get(
            "/monitoring/drift"
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["sample_count"] == 30
    assert payload["status"] == "healthy"

    assert (
        payload["features"]["air_temperature"]
        ["sample_count"]
        == 30
    )

    assert (
        payload["features"]["air_temperature"]
        ["status"]
        == "healthy"
    )


def test_drift_detects_major_temperature_shift(
    monkeypatch,
):
    with make_client(monkeypatch) as client:
        for _ in range(30):
            response = client.post(
                "/predict",
                json=make_payload(
                    air_temperature=50.0,
                    dew_temperature=45.0,
                ),
            )

            assert response.status_code == 200

        response = client.get(
            "/monitoring/drift"
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["sample_count"] == 30

    temperature = payload["features"][
        "air_temperature"
    ]

    assert temperature["psi"] is not None
    assert temperature["status"] == "critical"

    assert payload["status"] == "critical"