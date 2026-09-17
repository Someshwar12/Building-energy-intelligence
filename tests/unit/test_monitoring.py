from datetime import UTC, datetime, timedelta

from apps.model_service.app.monitoring import (
    MonitoringState,
    validate_prediction_request_data,
)
from apps.model_service.app.schemas import (
    EnergyObservation,
    PredictionRequest,
    PredictionResponse,
)


def make_request(
    energy_values: list[float] | None = None,
) -> PredictionRequest:
    start = datetime(2017, 12, 24, tzinfo=UTC)

    values = energy_values or [100.0] * 168

    history = [
        EnergyObservation(
            timestamp=start + timedelta(hours=index),
            energy_kwh=value,
        )
        for index, value in enumerate(values)
    ]

    return PredictionRequest(
        building_id="test_building",
        site_id="test_site",
        primary_use="Office",
        square_feet=10000.0,
        floor_area=10000.0,
        timezone="UTC",
        timestamp=start + timedelta(hours=168),
        air_temperature=10.0,
        dew_temperature=5.0,
        sea_level_pressure=1015.0,
        wind_direction=180.0,
        wind_speed=3.0,
        cloud_coverage=2.0,
        precip_depth_1_hr=0.0,
        history=history,
    )


def test_valid_prediction_history_is_healthy():
    result = validate_prediction_request_data(make_request())

    assert result["status"] == "healthy"
    assert result["failed_checks"] == []
    assert result["sample_count"] == 168


def test_duplicate_timestamps_are_detected():
    request = make_request()

    request.history[-1].timestamp = request.history[-2].timestamp

    result = validate_prediction_request_data(request)

    assert result["status"] == "warning"
    assert "duplicate_timestamps" in result["failed_checks"]


def test_monitoring_state_records_prediction():
    state = MonitoringState()

    request = make_request()

    response = PredictionResponse(
        building_id="test_building",
        timestamp=datetime.now(UTC),
        predicted_energy_kwh=123.45,
        model_name="test_model",
        model_version="1",
    )

    state.record_prediction(
        request,
        response,
        12.5,
    )

    snapshot = state.snapshot()

    assert snapshot["requests"]["total"] == 1
    assert snapshot["requests"]["successful"] == 1
    assert snapshot["requests"]["failed"] == 0
    assert snapshot["latency_ms"]["sample_count"] == 1
    assert snapshot["latency_ms"]["p50"] == 12.5
    assert snapshot["serving_modes"]["learned"] == 1
    assert snapshot["model_versions"]["1"] == 1
    assert snapshot["drift_observations"]["air_temperature"] == 1
    assert snapshot["drift_observations"]["dew_temperature"] == 1
    assert snapshot["drift_observations"]["square_feet"] == 1
    assert snapshot["drift_observations"]["floor_area"] == 1
    assert snapshot["drift_observations"]["energy_kwh"] == 1


def test_monitoring_state_records_failure():
    state = MonitoringState()

    state.record_failure("test failure")

    snapshot = state.snapshot()

    assert snapshot["requests"]["total"] == 1
    assert snapshot["requests"]["successful"] == 0
    assert snapshot["requests"]["failed"] == 1
    assert snapshot["last_error"] == "test failure"