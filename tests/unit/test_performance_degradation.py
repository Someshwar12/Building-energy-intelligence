from datetime import UTC, datetime, timedelta

from apps.model_service.app.performance import (
    DEFAULT_RECENT_WINDOW,
    PerformanceObservation,
    evaluate_degradation,
)


def observation(index: int, model_error: float, baseline_error: float) -> PerformanceObservation:
    actual = 100.0
    return PerformanceObservation(
        building_id="building-1",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=index),
        prediction=actual + model_error,
        actual=actual,
        persistence_baseline=actual + baseline_error,
        absolute_error=abs(model_error),
        squared_error=model_error**2,
        model_name="test_model",
        model_version="v1",
        serving_mode="learned",
    )


def test_sustained_degradation_requires_all_windows() -> None:
    observations = [
        observation(index, 20.0, 10.0)
        for index in range(DEFAULT_RECENT_WINDOW * 3)
    ]

    result = evaluate_degradation(observations)

    assert result["status"] == "degraded"
    assert result["sustained_degradation"] is True
    assert result["degraded_windows"] == 3


def test_one_bad_window_does_not_trigger_degradation() -> None:
    observations = [
        observation(index, 5.0, 10.0)
        for index in range(DEFAULT_RECENT_WINDOW * 2)
    ]
    observations.extend(
        observation(index, 20.0, 10.0)
        for index in range(DEFAULT_RECENT_WINDOW * 2, DEFAULT_RECENT_WINDOW * 3)
    )

    result = evaluate_degradation(observations)

    assert result["status"] == "healthy"
    assert result["sustained_degradation"] is False
    assert result["degraded_windows"] == 1


def test_degradation_requires_three_complete_windows() -> None:
    observations = [observation(index, 20.0, 10.0) for index in range(89)]

    result = evaluate_degradation(observations)

    assert result["status"] == "insufficient_data"
    assert result["sustained_degradation"] is False
