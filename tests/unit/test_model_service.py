from pathlib import Path

import pytest

from apps.model_service.app.inference import InferenceService
from apps.model_service.app.model_loader import ModelLoader


class FakeModel:
    def predict(self, frame):
        return [123.45]


class FakeLearnedLoader:
    model = FakeModel()
    model_name = "test_model"
    model_version = "phase1"
    serving_mode = "learned"

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


class FakeBaselineLoader:
    model_name = "persistence"
    model_version = "baseline"
    serving_mode = "baseline"


def make_request(timestamp):
    from datetime import UTC, datetime, timedelta

    from apps.model_service.app.schemas import PredictionRequest

    if timestamp is None:
        timestamp = datetime(
            2017,
            1,
            8,
            12,
            0,
            tzinfo=UTC,
        )

    history = [
        {
            "timestamp": timestamp - timedelta(hours=hours),
            "energy_kwh": float(100 + hours),
        }
        for hours in range(168, 0, -1)
    ]

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
        history=history,
    )


def test_inference_returns_learned_prediction():
    service = InferenceService(FakeLearnedLoader())

    response = service.predict(make_request(None))

    assert response.predicted_energy_kwh == 123.45
    assert response.model_name == "test_model"
    assert response.model_version == "phase1"


def test_baseline_prediction_uses_latest_observation():
    request = make_request(None)
    service = InferenceService(FakeBaselineLoader())

    response = service.predict(request)

    assert response.predicted_energy_kwh == request.history[-1].energy_kwh
    assert response.model_name == "persistence"
    assert response.model_version == "baseline"


def test_baseline_serving_mode_does_not_require_learned_model():
    request = make_request(None)
    service = InferenceService(FakeBaselineLoader())

    response = service.predict(request)

    assert response.predicted_energy_kwh >= 0
    assert response.model_name == "persistence"
    assert response.model_version == "baseline"


def test_model_loader_rejects_missing_artifact(tmp_path: Path):
    loader = ModelLoader(
        tmp_path / "missing_model.joblib",
    )

    with pytest.raises(
        FileNotFoundError,
        match="Model artifact not found",
    ):
        loader.initialize()


def test_model_loader_rejects_invalid_artifact(tmp_path: Path):
    artifact_path = tmp_path / "invalid_model.joblib"

    artifact_path.write_bytes(
        b"not a valid joblib artifact"
    )

    loader = ModelLoader(artifact_path)

    with pytest.raises(
        ValueError,
        match="Unable to load model artifact",
    ):
        loader.initialize()