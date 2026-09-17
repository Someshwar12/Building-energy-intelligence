from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite
from threading import Lock
from time import perf_counter
from typing import Any

from .drift import extract_monitoring_features
from .schemas import PredictionRequest, PredictionResponse

MAX_MONITORING_OBSERVATIONS = 1000


@dataclass
class MonitoringState:
    total_requests: int = 0
    successful_predictions: int = 0
    failed_predictions: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    model_versions: Counter[str] = field(default_factory=Counter)
    serving_modes: Counter[str] = field(default_factory=Counter)
    quality_checks: Counter[str] = field(default_factory=Counter)
    drift_observations: dict[str, list[float]] = field(
        default_factory=dict,
    )
    last_prediction_at: datetime | None = None
    last_error_at: datetime | None = None
    last_error: str | None = None
    _lock: Lock = field(default_factory=Lock, repr=False)

    def record_prediction(
        self,
        request: PredictionRequest,
        response: PredictionResponse,
        latency_ms: float,
    ) -> None:
        features = extract_monitoring_features(request)

        with self._lock:
            self.total_requests += 1
            self.successful_predictions += 1
            self.latencies_ms.append(latency_ms)

            self.model_versions[response.model_version] += 1
            self.last_prediction_at = (
                datetime.now().astimezone()
            )

            for feature, value in features.items():
                self.drift_observations.setdefault(
                    feature,
                    [],
                ).append(value)

                if (
                    len(self.drift_observations[feature])
                    > MAX_MONITORING_OBSERVATIONS
                ):
                    self.drift_observations[feature] = (
                        self.drift_observations[feature][
                            -MAX_MONITORING_OBSERVATIONS:
                        ]
                    )

            if len(self.latencies_ms) > MAX_MONITORING_OBSERVATIONS:
                self.latencies_ms = self.latencies_ms[
                    -MAX_MONITORING_OBSERVATIONS:
                ]

            if response.model_version == "baseline":
                self.serving_modes["baseline"] += 1
            else:
                self.serving_modes["learned"] += 1

    def record_failure(self, error: str) -> None:
        with self._lock:
            self.total_requests += 1
            self.failed_predictions += 1
            self.last_error_at = (
                datetime.now().astimezone()
            )
            self.last_error = error

    def record_quality(self, status: str) -> None:
        with self._lock:
            self.quality_checks[status] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            latencies = list(self.latencies_ms)

            if latencies:
                ordered = sorted(latencies)

                p50 = _percentile(
                    ordered,
                    0.50,
                )
                p95 = _percentile(
                    ordered,
                    0.95,
                )
                p99 = _percentile(
                    ordered,
                    0.99,
                )

                average = sum(latencies) / len(latencies)
            else:
                p50 = None
                p95 = None
                p99 = None
                average = None

            return {
                "requests": {
                    "total": self.total_requests,
                    "successful": self.successful_predictions,
                    "failed": self.failed_predictions,
                },
                "latency_ms": {
                    "sample_count": len(latencies),
                    "average": average,
                    "p50": p50,
                    "p95": p95,
                    "p99": p99,
                },
                "model_versions": dict(
                    self.model_versions,
                ),
                "serving_modes": dict(
                    self.serving_modes,
                ),
                "data_quality": dict(
                    self.quality_checks,
                ),
                "drift_observations": {
                    feature: len(values)
                    for feature, values
                    in self.drift_observations.items()
                },
                "last_prediction_at": (
                    self.last_prediction_at.isoformat()
                    if self.last_prediction_at
                    else None
                ),
                "last_error_at": (
                    self.last_error_at.isoformat()
                    if self.last_error_at
                    else None
                ),
                "last_error": self.last_error,
            }

    def get_drift_observations(self) -> dict[str, list[float]]:
        with self._lock:
            return {
                feature: list(values)
                for feature, values
                in self.drift_observations.items()
            }


def _percentile(
    values: list[float],
    percentile: float,
) -> float:
    if not values:
        raise ValueError(
            "Cannot calculate percentile for empty values."
        )

    position = (
        (len(values) - 1)
        * percentile
    )

    lower = int(position)

    upper = min(
        lower + 1,
        len(values) - 1,
    )

    if lower == upper:
        return values[lower]

    fraction = position - lower

    return (
        values[lower]
        + (
            values[upper]
            - values[lower]
        )
        * fraction
    )


def validate_prediction_request_data(
    request: PredictionRequest,
) -> dict[str, Any]:
    history = request.history

    energy_values = [
        observation.energy_kwh
        for observation in history
    ]

    timestamps = [
        observation.timestamp
        for observation in history
    ]

    duplicate_timestamps = (
        len(timestamps)
        - len(set(timestamps))
    )

    ordered = all(
        timestamps[index]
        < timestamps[index + 1]
        for index in range(
            len(timestamps) - 1
        )
    )

    hourly_intervals = [
        (
            timestamps[index + 1]
            - timestamps[index]
        ).total_seconds()
        / 3600
        for index in range(
            len(timestamps) - 1
        )
    ]

    frequency_ok = all(
        interval == 1.0
        for interval in hourly_intervals
    )

    finite_energy = all(
        isfinite(value)
        for value in energy_values
    )

    nonnegative_energy = all(
        value >= 0
        for value in energy_values
    )

    checks = {
        "history_length": len(history) >= 168,
        "duplicate_timestamps": (
            duplicate_timestamps == 0
        ),
        "chronological_order": ordered,
        "hourly_frequency": frequency_ok,
        "finite_energy": finite_energy,
        "nonnegative_energy": (
            nonnegative_energy
        ),
    }

    failed_checks = [
        name
        for name, passed in checks.items()
        if not passed
    ]

    status = (
        "warning"
        if failed_checks
        else "healthy"
    )

    return {
        "status": status,
        "checks": checks,
        "failed_checks": failed_checks,
        "sample_count": len(history),
        "duplicate_timestamps": duplicate_timestamps,
        "energy_min": (
            min(energy_values)
            if energy_values
            else None
        ),
        "energy_max": (
            max(energy_values)
            if energy_values
            else None
        ),
    }


def prediction_latency() -> float:
    return perf_counter()