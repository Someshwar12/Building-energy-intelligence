from __future__ import annotations

import math

import pandas as pd

from .model_loader import ModelLoader
from .schemas import PredictionRequest, PredictionResponse


class InferenceService:
    """Transforms validated API requests into model predictions."""

    def __init__(self, model_loader: ModelLoader) -> None:
        self.model_loader = model_loader

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        features = self._build_features(request)

        feature_frame = pd.DataFrame(
            [features],
            columns=self.model_loader.feature_columns,
        )

        prediction = float(
            self.model_loader.model.predict(feature_frame)[0]
        )

        return PredictionResponse(
            building_id=request.building_id,
            timestamp=request.timestamp,
            predicted_energy_kwh=prediction,
            model_name=self.model_loader.model_name,
            model_version=self.model_loader.model_version,
        )

    def _build_features(
        self,
        request: PredictionRequest,
    ) -> dict:
        history = (
            pd.DataFrame(
                [
                    {
                        "timestamp": item.timestamp,
                        "energy_kwh": item.energy_kwh,
                    }
                    for item in request.history
                ]
            )
            .sort_values("timestamp")
            .set_index("timestamp")
        )

        energy = history["energy_kwh"]
        timestamp = request.timestamp

        expected_timestamps = pd.date_range(
            start=timestamp - pd.Timedelta(hours=168),
            end=timestamp - pd.Timedelta(hours=1),
            freq="h",
        )

        if not energy.index.equals(expected_timestamps):
            raise ValueError(
                "history must contain exactly 168 consecutive hourly "
                "observations immediately before prediction timestamp"
            )

        day_of_year = timestamp.timetuple().tm_yday

        def lag(hours: int) -> float:
            target_time = timestamp - pd.Timedelta(hours=hours)
            return float(energy.loc[target_time])

        # Phase 1 uses strictly past data for rolling features.
        recent = energy[
            (energy.index >= timestamp - pd.Timedelta(hours=3))
            & (energy.index < timestamp)
        ]

        recent_6h = energy[
            (energy.index >= timestamp - pd.Timedelta(hours=6))
            & (energy.index < timestamp)
        ]

        recent_24h = energy[
            (energy.index >= timestamp - pd.Timedelta(hours=24))
            & (energy.index < timestamp)
        ]

        recent_168h = energy[
            (energy.index >= timestamp - pd.Timedelta(hours=168))
            & (energy.index < timestamp)
        ]

        if len(recent) != 3:
            raise ValueError(
                "history must contain 3 complete hourly observations"
            )

        if len(recent_6h) != 6:
            raise ValueError(
                "history must contain 6 complete hourly observations"
            )

        if len(recent_24h) != 24:
            raise ValueError(
                "history must contain 24 complete hourly observations"
            )

        if len(recent_168h) != 168:
            raise ValueError(
                "history must contain 168 complete hourly observations"
            )

        temperature = request.air_temperature

        if temperature is None:
            heating_degree_hour = float("nan")
            cooling_degree_hour = float("nan")
        else:
            heating_degree_hour = max(0.0, 18.0 - temperature)
            cooling_degree_hour = max(0.0, temperature - 18.0)

        return {
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
            "hour": timestamp.hour,
            "day_of_week": timestamp.weekday(),
            "month": timestamp.month,
            "day_of_year": day_of_year,
            "is_weekend": int(timestamp.weekday() >= 5),
            "hour_sin": math.sin(
                2 * math.pi * timestamp.hour / 24.0
            ),
            "hour_cos": math.cos(
                2 * math.pi * timestamp.hour / 24.0
            ),
            "day_of_year_sin": math.sin(
                2 * math.pi * day_of_year / 365.25
            ),
            "day_of_year_cos": math.cos(
                2 * math.pi * day_of_year / 365.25
            ),
            "energy_lag_1h": lag(1),
            "energy_lag_2h": lag(2),
            "energy_lag_3h": lag(3),
            "energy_lag_24h": lag(24),
            "energy_lag_48h": lag(48),
            "energy_lag_72h": lag(72),
            "energy_lag_168h": lag(168),
            "energy_roll_mean_3h": float(recent.mean()),
            "energy_roll_mean_6h": float(recent_6h.mean()),
            "energy_roll_mean_24h": float(recent_24h.mean()),
            "energy_roll_max_24h": float(recent_24h.max()),
            "energy_roll_mean_168h": float(recent_168h.mean()),
            "energy_roll_max_168h": float(recent_168h.max()),
            "heating_degree_hour": heating_degree_hour,
            "cooling_degree_hour": cooling_degree_hour,
        }