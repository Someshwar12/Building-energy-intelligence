from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import apps.model_service.app.main as main_module
from apps.model_service.app.inference import InferenceService


class FakeModel:
    def predict(self, features):
        return [123.45]


class FakeLoader:
    model_name = "test_model"
    model_version = "phase5-test"
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


class FakeUnreadyLoader(FakeLoader):
    @property
    def is_ready(self):
        return False


class FakeBaselineLoader(FakeLoader):
    model_name = "persistence"
    model_version = "baseline"
    serving_mode = "baseline"

    @property
    def model(self):
        raise AssertionError(
            "Baseline serving must not access a learned model."
        )


@pytest.fixture
def client(monkeypatch):
    loader = FakeLoader()

    monkeypatch.setattr(
        main_module,
        "model_loader",
        loader,
    )
    monkeypatch.setattr(
        main_module,
        "inference_service",
        InferenceService(loader),
    )

    with TestClient(main_module.app) as test_client:
        yield test_client


@pytest.fixture
def unready_client(monkeypatch):
    loader = FakeUnreadyLoader()

    monkeypatch.setattr(
        main_module,
        "model_loader",
        loader,
    )
    monkeypatch.setattr(
        main_module,
        "inference_service",
        InferenceService(loader),
    )

    with TestClient(main_module.app) as test_client:
        yield test_client


@pytest.fixture
def baseline_client(monkeypatch):
    loader = FakeBaselineLoader()

    monkeypatch.setattr(
        main_module,
        "model_loader",
        loader,
    )
    monkeypatch.setattr(
        main_module,
        "inference_service",
        InferenceService(loader),
    )

    with TestClient(main_module.app) as test_client:
        yield test_client


def make_payload(history_count=168):
    start = datetime(
        2017,
        12,
        24,
        0,
        0,
        tzinfo=UTC,
    )

    history = []

    for index in range(history_count):
        history.append(
            {
                "timestamp": (
                    start + timedelta(hours=index)
                ).isoformat(),
                "energy_kwh": 100.0 + index,
            }
        )

    prediction_timestamp = (
        start + timedelta(hours=history_count)
    ).isoformat()

    return {
        "building_id": "test_building",
        "site_id": "test_site",
        "primary_use": "Office",
        "square_feet": 10000.0,
        "floor_area": 10000.0,
        "timezone": "UTC",
        "timestamp": prediction_timestamp,
        "air_temperature": 10.0,
        "dew_temperature": 5.0,
        "sea_level_pressure": 1015.0,
        "wind_direction": 180.0,
        "wind_speed": 3.0,
        "cloud_coverage": 2.0,
        "precip_depth_1_hr": 0.0,
        "history": history,
    }


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"


def test_ready_endpoint(client):
    response = client.get("/ready")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ready"
    assert body["model_name"] == "test_model"
    assert body["model_version"] == "phase5-test"
    assert body["serving_mode"] == "learned"


def test_predict_endpoint(client):
    response = client.post(
        "/predict",
        json=make_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["building_id"] == "test_building"
    assert body["predicted_energy_kwh"] == pytest.approx(123.45)
    assert body["model_name"] == "test_model"
    assert body["model_version"] == "phase5-test"


def test_predict_rejects_incomplete_history(client):
    response = client.post(
        "/predict",
        json=make_payload(history_count=167),
    )

    assert response.status_code == 422


def test_predict_rejects_non_consecutive_history(client):
    payload = make_payload()

    payload["history"][100]["timestamp"] = (
        datetime(
            2017,
            12,
            24,
            0,
            0,
            tzinfo=UTC,
        )
        + timedelta(hours=102)
    ).isoformat()

    response = client.post(
        "/predict",
        json=payload,
    )

    assert response.status_code == 422


def test_predict_rejects_negative_energy_history(client):
    payload = make_payload()
    payload["history"][50]["energy_kwh"] = -1.0

    response = client.post(
        "/predict",
        json=payload,
    )

    assert response.status_code == 422


def test_predict_rejects_invalid_building_metadata(client):
    payload = make_payload()
    payload["square_feet"] = 0

    response = client.post(
        "/predict",
        json=payload,
    )

    assert response.status_code == 422


def test_predict_rejects_when_service_is_not_ready(
    unready_client,
):
    response = unready_client.post(
        "/predict",
        json=make_payload(),
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Model service is not ready."
    )


def test_ready_reports_unready_service(unready_client):
    response = unready_client.get("/ready")

    assert response.status_code == 503


def test_predict_endpoint_uses_baseline_serving_mode(
    baseline_client,
):
    payload = make_payload()

    response = baseline_client.post(
        "/predict",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["building_id"] == "test_building"
    assert body["predicted_energy_kwh"] == 267.0
    assert body["model_name"] == "persistence"
    assert body["model_version"] == "baseline"