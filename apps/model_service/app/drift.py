from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .schemas import PredictionRequest

REFERENCE_PROFILE_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "monitoring_reference.json"
)

DRIFT_WARNING_PSI = 0.10
DRIFT_CRITICAL_PSI = 0.25
MIN_DRIFT_SAMPLE_COUNT = 30
EPSILON = 1e-6


@dataclass(frozen=True)
class DriftResult:
    feature: str
    psi: float | None
    status: str
    sample_count: int
    reference_available: bool


def _status_from_psi(psi: float) -> str:
    if psi >= DRIFT_CRITICAL_PSI:
        return "critical"

    if psi >= DRIFT_WARNING_PSI:
        return "warning"

    return "healthy"


def _quantile_bins(reference: np.ndarray) -> np.ndarray:
    reference = np.asarray(reference, dtype=float)

    minimum = float(np.min(reference))
    maximum = float(np.max(reference))

    if minimum == maximum:
        return np.array(
            [
                -np.inf,
                minimum - EPSILON,
                minimum + EPSILON,
                np.inf,
            ]
        )

    quantiles = np.quantile(
        reference,
        np.linspace(0.0, 1.0, 11),
    )

    internal_bins = np.unique(
        quantiles[1:-1]
    )

    if len(internal_bins) == 0:
        return np.array(
            [
                -np.inf,
                minimum,
                maximum,
                np.inf,
            ]
        )

    return np.concatenate(
        [
            [-np.inf],
            internal_bins,
            [np.inf],
        ]
    )


def _distribution(
    values: np.ndarray,
    bins: np.ndarray,
) -> np.ndarray:
    counts, _ = np.histogram(
        values,
        bins=bins,
    )

    probabilities = counts.astype(float)

    total = probabilities.sum()

    if total <= 0:
        raise ValueError(
            "Distribution contains no usable observations."
        )

    probabilities /= total
    probabilities = np.clip(
        probabilities,
        EPSILON,
        None,
    )

    return probabilities / probabilities.sum()


def calculate_psi(
    reference: list[float] | np.ndarray,
    current: list[float] | np.ndarray,
) -> float:
    reference_array = np.asarray(
        reference,
        dtype=float,
    )
    current_array = np.asarray(
        current,
        dtype=float,
    )

    if reference_array.size == 0:
        raise ValueError(
            "Reference distribution is empty."
        )

    if current_array.size == 0:
        raise ValueError(
            "Current distribution is empty."
        )

    reference_array = reference_array[
        np.isfinite(reference_array)
    ]
    current_array = current_array[
        np.isfinite(current_array)
    ]

    if reference_array.size == 0:
        raise ValueError(
            "Reference distribution contains no finite values."
        )

    if current_array.size == 0:
        raise ValueError(
            "Current distribution contains no finite values."
        )

    reference_min = float(
        np.min(reference_array)
    )
    reference_max = float(
        np.max(reference_array)
    )

    if reference_min == reference_max:
        reference_value = reference_min

        current_deviation = np.abs(
            current_array - reference_value
        )

        if np.all(
            current_deviation <= EPSILON
        ):
            return 0.0

        return float(
            np.mean(
                current_deviation
                / max(
                    abs(reference_value),
                    1.0,
                )
            )
            * 10.0
        )

    bins = _quantile_bins(
        reference_array
    )

    reference_distribution = _distribution(
        reference_array,
        bins,
    )

    current_distribution = _distribution(
        current_array,
        bins,
    )

    psi = np.sum(
        (
            current_distribution
            - reference_distribution
        )
        * np.log(
            current_distribution
            / reference_distribution
        )
    )

    return float(psi)


def load_reference_profile() -> dict[str, Any]:
    if not REFERENCE_PROFILE_PATH.exists():
        return {
            "available": False,
            "source": None,
            "sample_count": 0,
            "features": {},
        }

    try:
        with REFERENCE_PROFILE_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            profile = json.load(file)
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {
            "available": False,
            "source": None,
            "sample_count": 0,
            "features": {},
        }

    return profile


def extract_monitoring_features(
    request: PredictionRequest,
) -> dict[str, float]:
    history = request.history

    energy_values = np.asarray(
        [
            observation.energy_kwh
            for observation in history
        ],
        dtype=float,
    )

    timestamp = request.timestamp

    features: dict[str, float] = {
        "square_feet": float(
            request.square_feet
        ),
        "floor_area": float(
            request.floor_area
        ),
        "hour": float(timestamp.hour),
        "day_of_week": float(
            timestamp.weekday()
        ),
        "month": float(timestamp.month),
        "day_of_year": float(
            timestamp.timetuple().tm_yday
        ),
        "is_weekend": float(
            timestamp.weekday() >= 5
        ),
        "energy_kwh": float(
            energy_values[-1]
        ),
        "energy_lag_1h": float(
            energy_values[-1]
        ),
        "energy_lag_2h": float(
            energy_values[-2]
        ),
        "energy_lag_3h": float(
            energy_values[-3]
        ),
        "energy_lag_24h": float(
            energy_values[-24]
        ),
        "energy_lag_48h": float(
            energy_values[-48]
        ),
        "energy_lag_72h": float(
            energy_values[-72]
        ),
        "energy_lag_168h": float(
            energy_values[-168]
        ),
        "energy_roll_mean_3h": float(
            np.mean(energy_values[-3:])
        ),
        "energy_roll_mean_6h": float(
            np.mean(energy_values[-6:])
        ),
        "energy_roll_mean_24h": float(
            np.mean(energy_values[-24:])
        ),
        "energy_roll_max_24h": float(
            np.max(energy_values[-24:])
        ),
        "energy_roll_mean_168h": float(
            np.mean(energy_values[-168:])
        ),
        "energy_roll_max_168h": float(
            np.max(energy_values[-168:])
        ),
    }

    optional_weather_features = {
        "air_temperature": request.air_temperature,
        "dew_temperature": request.dew_temperature,
        "cloud_coverage": request.cloud_coverage,
        "wind_speed": request.wind_speed,
        "wind_direction": request.wind_direction,
        "sea_level_pressure": request.sea_level_pressure,
        "precip_depth_1_hr": request.precip_depth_1_hr,
    }

    for feature, value in optional_weather_features.items():
        if value is not None:
            features[feature] = float(value)

    if request.air_temperature is not None:
        air_temperature = float(
            request.air_temperature
        )

        features["heating_degree_hour"] = float(
            max(
                18.0 - air_temperature,
                0.0,
            )
        )

        features["cooling_degree_hour"] = float(
            max(
                air_temperature - 18.0,
                0.0,
            )
        )

    return features


def calculate_feature_drift(
    feature: str,
    current_values: list[float],
    reference_values: list[float],
) -> DriftResult:
    current_array = np.asarray(
        current_values,
        dtype=float,
    )

    reference_array = np.asarray(
        reference_values,
        dtype=float,
    )

    current_array = current_array[
        np.isfinite(current_array)
    ]

    reference_array = reference_array[
        np.isfinite(reference_array)
    ]

    sample_count = int(
        current_array.size
    )

    if sample_count < MIN_DRIFT_SAMPLE_COUNT:
        return DriftResult(
            feature=feature,
            psi=None,
            status="insufficient_data",
            sample_count=sample_count,
            reference_available=(
                reference_array.size > 0
            ),
        )

    if reference_array.size == 0:
        return DriftResult(
            feature=feature,
            psi=None,
            status="reference_unavailable",
            sample_count=sample_count,
            reference_available=False,
        )

    psi = calculate_psi(
        reference=reference_array,
        current=current_array,
    )

    return DriftResult(
        feature=feature,
        psi=psi,
        status=_status_from_psi(psi),
        sample_count=sample_count,
        reference_available=True,
    )


def evaluate_request_drift(
    request: PredictionRequest,
    reference_profile: dict[str, Any],
) -> dict[str, DriftResult]:
    current_features = (
        extract_monitoring_features(request)
    )

    reference_features = reference_profile.get(
        "features",
        {},
    )

    results: dict[str, DriftResult] = {}

    for feature, value in current_features.items():
        reference_values = reference_features.get(
            feature,
            {},
        ).get(
            "values",
            [],
        )

        results[feature] = calculate_feature_drift(
            feature=feature,
            current_values=[value],
            reference_values=reference_values,
        )

    return results