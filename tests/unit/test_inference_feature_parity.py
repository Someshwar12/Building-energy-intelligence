from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from apps.model_service.app.inference import InferenceService
from apps.model_service.app.schemas import PredictionRequest
from ml.features.build import build_features


class FakeModel:
    def predict(self, frame):
        return [0.0]


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


def make_request(timestamp: datetime) -> PredictionRequest:
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


def test_api_features_match_phase1_feature_builder():
    timestamp = datetime(2017, 1, 8, 12, 0, tzinfo=UTC)
    request = make_request(timestamp)

    service = InferenceService(FakeLoader())

    api_features = service._build_features(request)

    history_frame = pd.DataFrame(
        [
            {
                "timestamp": item.timestamp,
                "building_id": request.building_id,
                "energy_kwh": item.energy_kwh,
            }
            for item in request.history
        ]
    )

    history_frame["site_id"] = request.site_id
    history_frame["primary_use"] = request.primary_use
    history_frame["square_feet"] = request.square_feet
    history_frame["floor_area"] = request.floor_area
    history_frame["timezone"] = request.timezone
    history_frame["air_temperature"] = request.air_temperature
    history_frame["dew_temperature"] = request.dew_temperature
    history_frame["cloud_coverage"] = request.cloud_coverage
    history_frame["wind_speed"] = request.wind_speed
    history_frame["wind_direction"] = request.wind_direction
    history_frame["sea_level_pressure"] = request.sea_level_pressure
    history_frame["precip_depth_1_hr"] = request.precip_depth_1_hr

    phase1 = build_features(
        history_frame,
        lags=(1, 2, 3, 24, 48, 72, 168),
        rolling_windows=(3, 6, 24, 168),
        degree_day_base_c=18.0,
        target_name="target_next_hour_kwh",
    )

    phase1_row = phase1.loc[
        phase1["timestamp"] == pd.Timestamp(timestamp)
    ]

    # The API predicts timestamp t using history through t-1.
    # Therefore append the prediction timestamp with a placeholder
    # energy value so the Phase 1 feature builder can construct
    # features at t. The placeholder must not affect strictly-past
    # rolling features or lag features.
    prediction_row = pd.DataFrame(
        [
            {
                "timestamp": timestamp,
                "building_id": request.building_id,
                "site_id": request.site_id,
                "primary_use": request.primary_use,
                "square_feet": request.square_feet,
                "floor_area": request.floor_area,
                "timezone": request.timezone,
                "air_temperature": request.air_temperature,
                "dew_temperature": request.dew_temperature,
                "cloud_coverage": request.cloud_coverage,
                "wind_speed": request.wind_speed,
                "wind_direction": request.wind_direction,
                "sea_level_pressure": request.sea_level_pressure,
                "precip_depth_1_hr": request.precip_depth_1_hr,
                "energy_kwh": float("nan"),
            }
        ]
    )

    phase1_input = pd.concat(
        [history_frame, prediction_row],
        ignore_index=True,
    )

    phase1 = build_features(
        phase1_input,
        lags=(1, 2, 3, 24, 48, 72, 168),
        rolling_windows=(3, 6, 24, 168),
        degree_day_base_c=18.0,
        target_name="target_next_hour_kwh",
    )

    phase1_row = phase1.loc[
        phase1["timestamp"] == pd.Timestamp(timestamp)
    ].iloc[0]

    comparable_columns = [
        column
        for column in FakeLoader.feature_columns
        if column in phase1.columns
    ]

    for column in comparable_columns:
        api_value = api_features[column]
        phase1_value = phase1_row[column]

        if pd.isna(phase1_value):
            assert pd.isna(api_value), column
        else:
            assert api_value == pytest.approx(
                phase1_value,
                rel=1e-12,
                abs=1e-12,
            ), column