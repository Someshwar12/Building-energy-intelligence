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
    monkeypatch.setattr(
        main_module,
        "performance_state",
        main_module.PerformanceState(),
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
    monkeypatch.setattr(
        main_module,
        "performance_state",
        main_module.PerformanceState(),
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
    monkeypatch.setattr(
        main_module,
        "performance_state",
        main_module.PerformanceState(),
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


def test_prediction_creates_pending_performance_observation(
    client,
):
    response = client.post(
        "/predict",
        json=make_payload(),
    )

    assert response.status_code == 200

    summary = client.get(
        "/monitoring/summary"
    ).json()

    assert summary["monitoring"]["performance"] == {
        "pending_predictions": 1,
        "completed_outcomes": 0,
    }


def test_outcome_records_prediction_error(client):
    payload = make_payload()

    prediction_response = client.post(
        "/predict",
        json=payload,
    )

    assert prediction_response.status_code == 200

    outcome_response = client.post(
        "/monitoring/outcomes",
        json={
            "building_id": "test_building",
            "timestamp": payload["timestamp"],
            "actual_energy_kwh": 120.0,
        },
    )

    assert outcome_response.status_code == 200

    body = outcome_response.json()

    assert body["status"] == "recorded"
    assert body["outcome"]["prediction"] == pytest.approx(
        123.45
    )
    assert body["outcome"]["actual"] == pytest.approx(
        120.0
    )
    assert body["outcome"]["persistence_baseline"] == pytest.approx(
        267.0
    )
    assert body["outcome"]["absolute_error"] == pytest.approx(
        3.45
    )
    assert body["outcome"]["squared_error"] == pytest.approx(
        3.45**2
    )
    assert body["outcome"]["model_version"] == "phase5-test"
    assert body["outcome"]["serving_mode"] == "learned"

    summary = client.get(
        "/monitoring/summary"
    ).json()

    assert summary["monitoring"]["performance"] == {
        "pending_predictions": 0,
        "completed_outcomes": 1,
    }


def test_outcome_requires_existing_prediction(client):
    response = client.post(
        "/monitoring/outcomes",
        json={
            "building_id": "unknown_building",
            "timestamp": (
                datetime(
                    2020,
                    1,
                    1,
                    tzinfo=UTC,
                ).isoformat()
            ),
            "actual_energy_kwh": 100.0,
        },
    )

    assert response.status_code == 404


def test_outcome_rejects_negative_actual_energy(client):
    response = client.post(
        "/monitoring/outcomes",
        json={
            "building_id": "test_building",
            "timestamp": (
                datetime(
                    2020,
                    1,
                    1,
                    tzinfo=UTC,
                ).isoformat()
            ),
            "actual_energy_kwh": -1.0,
        },
    )

    assert response.status_code == 422

def test_performance_endpoint_reports_metrics(client):
    payload = make_payload()

    prediction_response = client.post(
        "/predict",
        json=payload,
    )
    assert prediction_response.status_code == 200

    outcome_response = client.post(
        "/monitoring/outcomes",
        json={
            "building_id": payload["building_id"],
            "timestamp": payload["timestamp"],
            "actual_energy_kwh": 120.0,
        },
    )
    assert outcome_response.status_code == 200

    response = client.get("/monitoring/performance")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "insufficient_data"
    assert body["sample_count"] == 1
    assert body["recent"]["mae"] == pytest.approx(3.45)
    assert body["comparison"]["beats_baseline"] is True


def test_performance_endpoint_detects_baseline_underperformance(client):
    for index in range(90):
        payload = make_payload()

        timestamp = (
            datetime(2018, 1, 1, tzinfo=UTC)
            + timedelta(hours=index)
        )

        payload["timestamp"] = timestamp.isoformat()

        history_start = timestamp - timedelta(hours=168)

        payload["history"] = [
            {
                "timestamp": (
                    history_start + timedelta(hours=hour)
                ).isoformat(),
                "energy_kwh": 100.0,
            }
            for hour in range(168)
        ]

        prediction_response = client.post(
            "/predict",
            json=payload,
        )

        assert prediction_response.status_code == 200

        outcome_response = client.post(
            "/monitoring/outcomes",
            json={
                "building_id": payload["building_id"],
                "timestamp": payload["timestamp"],
                "actual_energy_kwh": 100.0,
            },
        )

        assert outcome_response.status_code == 200

    response = client.get("/monitoring/performance")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "degraded"
    assert body["degradation"]["sustained_degradation"] is True
    assert body["degradation"]["completed_windows"] == 3
    assert body["degradation"]["degraded_windows"] == 3


def test_performance_endpoint_rejects_invalid_window(client):
    response = client.get("/monitoring/performance?recent_window=0")
    assert response.status_code == 400
