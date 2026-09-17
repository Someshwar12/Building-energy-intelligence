from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import sqrt
from threading import Lock
from typing import Any

MAX_PERFORMANCE_OBSERVATIONS = 1000
MIN_PERFORMANCE_SAMPLE_COUNT = 30
DEFAULT_RECENT_WINDOW = 30
SUSTAINED_DEGRADATION_WINDOWS = 3
DEGRADATION_RELATIVE_THRESHOLD_PCT = 10.0


@dataclass(frozen=True)
class PredictionRecord:
    building_id: str
    timestamp: datetime
    prediction: float
    persistence_baseline: float
    model_name: str
    model_version: str
    serving_mode: str


@dataclass(frozen=True)
class PerformanceObservation:
    building_id: str
    timestamp: datetime
    prediction: float
    actual: float
    persistence_baseline: float
    absolute_error: float
    squared_error: float
    model_name: str
    model_version: str
    serving_mode: str


class PerformanceState:
    """Tracks predictions until their actual outcomes become available."""

    def __init__(self) -> None:
        self._pending: dict[tuple[str, datetime], PredictionRecord] = {}
        self._observations: list[PerformanceObservation] = []
        self._lock = Lock()

    def record_prediction(
        self,
        building_id: str,
        timestamp: datetime,
        prediction: float,
        persistence_baseline: float,
        model_name: str,
        model_version: str,
        serving_mode: str,
    ) -> None:
        record = PredictionRecord(
            building_id=building_id,
            timestamp=timestamp,
            prediction=float(prediction),
            persistence_baseline=float(persistence_baseline),
            model_name=model_name,
            model_version=model_version,
            serving_mode=serving_mode,
        )

        key = (building_id, timestamp)

        with self._lock:
            self._pending[key] = record

            if len(self._pending) > MAX_PERFORMANCE_OBSERVATIONS:
                oldest_key = min(
                    self._pending,
                    key=lambda item: item[1],
                )
                del self._pending[oldest_key]

    def record_outcome(
        self,
        building_id: str,
        timestamp: datetime,
        actual_energy_kwh: float,
    ) -> PerformanceObservation:
        key = (building_id, timestamp)

        with self._lock:
            record = self._pending.get(key)

            if record is None:
                raise ValueError(
                    "No pending prediction exists for the supplied "
                    "building_id and timestamp."
                )

            actual = float(actual_energy_kwh)
            absolute_error = abs(record.prediction - actual)
            squared_error = (record.prediction - actual) ** 2

            observation = PerformanceObservation(
                building_id=record.building_id,
                timestamp=record.timestamp,
                prediction=record.prediction,
                actual=actual,
                persistence_baseline=record.persistence_baseline,
                absolute_error=absolute_error,
                squared_error=squared_error,
                model_name=record.model_name,
                model_version=record.model_version,
                serving_mode=record.serving_mode,
            )

            del self._pending[key]
            self._observations.append(observation)

            if len(self._observations) > MAX_PERFORMANCE_OBSERVATIONS:
                self._observations = self._observations[
                    -MAX_PERFORMANCE_OBSERVATIONS:
                ]

            return observation

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "pending_predictions": len(self._pending),
                "completed_outcomes": len(self._observations),
            }

    def get_observations(self) -> list[PerformanceObservation]:
        with self._lock:
            return list(self._observations)

    def performance_report(
        self,
        recent_window: int = DEFAULT_RECENT_WINDOW,
    ) -> dict[str, Any]:
        if recent_window < 1:
            raise ValueError("recent_window must be at least 1.")

        observations = self.get_observations()
        observations.sort(key=lambda observation: observation.timestamp)

        recent = observations[-recent_window:]

        overall_metrics = calculate_performance_metrics(observations)
        recent_metrics = calculate_performance_metrics(recent)
        per_building = calculate_per_building_metrics(recent)
        comparison = compare_with_persistence(recent)

        degradation = evaluate_degradation(
            observations,
            recent_window=recent_window,
            sustained_windows=SUSTAINED_DEGRADATION_WINDOWS,
            relative_threshold_pct=DEGRADATION_RELATIVE_THRESHOLD_PCT,
        )

        return {
            "status": degradation["status"],
            "sample_count": len(recent),
            "minimum_sample_count": MIN_PERFORMANCE_SAMPLE_COUNT,
            "recent_window": recent_window,
            "overall": overall_metrics,
            "recent": recent_metrics,
            "comparison": comparison,
            "degradation": degradation,
            "per_building": per_building,
        }


def _metrics_from_errors(
    absolute_errors: list[float],
    squared_errors: list[float],
    actuals: list[float],
) -> dict[str, float | None]:
    if not absolute_errors:
        return {
            "mae": None,
            "rmse": None,
            "nmae": None,
        }

    mae = sum(absolute_errors) / len(absolute_errors)
    rmse = sqrt(sum(squared_errors) / len(squared_errors))
    mean_actual = sum(actuals) / len(actuals)
    nmae = mae / mean_actual if mean_actual > 0 else None

    return {
        "mae": mae,
        "rmse": rmse,
        "nmae": nmae,
    }


def calculate_performance_metrics(
    observations: list[PerformanceObservation],
) -> dict[str, float | int | None]:
    model_metrics = _metrics_from_errors(
        [observation.absolute_error for observation in observations],
        [observation.squared_error for observation in observations],
        [observation.actual for observation in observations],
    )

    baseline_absolute_errors = [
        abs(observation.persistence_baseline - observation.actual)
        for observation in observations
    ]

    baseline_squared_errors = [
        (observation.persistence_baseline - observation.actual) ** 2
        for observation in observations
    ]

    baseline_metrics = _metrics_from_errors(
        baseline_absolute_errors,
        baseline_squared_errors,
        [observation.actual for observation in observations],
    )

    return {
        "sample_count": len(observations),
        **model_metrics,
        "persistence_mae": baseline_metrics["mae"],
        "persistence_rmse": baseline_metrics["rmse"],
        "persistence_nmae": baseline_metrics["nmae"],
    }


def calculate_per_building_metrics(
    observations: list[PerformanceObservation],
) -> dict[str, dict[str, float | int | None]]:
    grouped: dict[str, list[PerformanceObservation]] = {}

    for observation in observations:
        grouped.setdefault(observation.building_id, []).append(observation)

    return {
        building_id: calculate_performance_metrics(building_observations)
        for building_id, building_observations in sorted(grouped.items())
    }


def compare_with_persistence(
    observations: list[PerformanceObservation],
) -> dict[str, float | bool | None]:
    metrics = calculate_performance_metrics(observations)

    model_nmae = metrics["nmae"]
    baseline_nmae = metrics["persistence_nmae"]

    if model_nmae is None or baseline_nmae is None:
        return {
            "model_nmae": model_nmae,
            "baseline_nmae": baseline_nmae,
            "nmae_delta": None,
            "relative_change_pct": None,
            "beats_baseline": None,
        }

    delta = model_nmae - baseline_nmae

    relative_change_pct = (
        delta / baseline_nmae * 100
        if baseline_nmae > 0
        else None
    )

    return {
        "model_nmae": model_nmae,
        "baseline_nmae": baseline_nmae,
        "nmae_delta": delta,
        "relative_change_pct": relative_change_pct,
        "beats_baseline": model_nmae < baseline_nmae,
    }


def _evaluate_window(
    observations: list[PerformanceObservation],
    relative_threshold_pct: float,
) -> dict[str, Any]:
    metrics = compare_with_persistence(observations)

    model_nmae = metrics["model_nmae"]
    baseline_nmae = metrics["baseline_nmae"]
    relative_change_pct = metrics["relative_change_pct"]

    if model_nmae is None or baseline_nmae is None:
        degraded = None
    elif baseline_nmae == 0:
        degraded = model_nmae > 0
    else:
        degraded = (
            relative_change_pct is not None
            and relative_change_pct >= relative_threshold_pct
        )

    return {
        "sample_count": len(observations),
        "model_nmae": model_nmae,
        "baseline_nmae": baseline_nmae,
        "relative_change_pct": relative_change_pct,
        "degraded": degraded,
    }


def evaluate_degradation(
    observations: list[PerformanceObservation],
    recent_window: int = DEFAULT_RECENT_WINDOW,
    sustained_windows: int = SUSTAINED_DEGRADATION_WINDOWS,
    relative_threshold_pct: float = DEGRADATION_RELATIVE_THRESHOLD_PCT,
) -> dict[str, Any]:
    """Evaluate sustained degradation against persistence."""

    if recent_window < 1:
        raise ValueError("recent_window must be at least 1.")

    if sustained_windows < 1:
        raise ValueError("sustained_windows must be at least 1.")

    if relative_threshold_pct < 0:
        raise ValueError("relative_threshold_pct cannot be negative.")

    ordered = sorted(
        observations,
        key=lambda observation: observation.timestamp,
    )

    required_samples = recent_window * sustained_windows

    if len(ordered) < required_samples:
        return {
            "status": "insufficient_data",
            "sample_count": len(ordered),
            "minimum_sample_count": MIN_PERFORMANCE_SAMPLE_COUNT,
            "required_window_samples": required_samples,
            "sustained_windows": sustained_windows,
            "completed_windows": 0,
            "degraded_windows": 0,
            "relative_threshold_pct": relative_threshold_pct,
            "current_window_degraded": None,
            "sustained_degradation": False,
            "reason": (
                "Not enough completed outcomes for sustained "
                "degradation evaluation."
            ),
            "windows": [],
        }

    selected = ordered[-required_samples:]
    windows: list[dict[str, Any]] = []

    for index in range(sustained_windows):
        start = index * recent_window
        end = start + recent_window
        window = selected[start:end]

        evaluation = _evaluate_window(
            window,
            relative_threshold_pct,
        )

        windows.append(
            {
                "index": index + 1,
                **evaluation,
            }
        )

    degraded_windows = sum(
        window["degraded"] is True
        for window in windows
    )

    evaluable_windows = sum(
        window["degraded"] is not None
        for window in windows
    )

    current_window_degraded = windows[-1]["degraded"]

    if evaluable_windows < sustained_windows:
        status = "insufficient_data"
        sustained = False
        reason = (
            "One or more sustained evaluation windows lack "
            "valid performance metrics."
        )
    else:
        sustained = degraded_windows == sustained_windows

        if sustained:
            status = "degraded"
            reason = (
                "Model underperformed persistence across all "
                "sustained windows."
            )
        else:
            status = "healthy"
            reason = (
                "Sustained degradation was not observed across "
                "all windows."
            )

    return {
        "status": status,
        "sample_count": len(ordered),
        "minimum_sample_count": MIN_PERFORMANCE_SAMPLE_COUNT,
        "required_window_samples": required_samples,
        "sustained_windows": sustained_windows,
        "completed_windows": len(windows),
        "degraded_windows": degraded_windows,
        "relative_threshold_pct": relative_threshold_pct,
        "current_window_degraded": current_window_degraded,
        "sustained_degradation": sustained,
        "reason": reason,
        "windows": windows,
    }