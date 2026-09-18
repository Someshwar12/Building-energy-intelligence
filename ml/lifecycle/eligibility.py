from __future__ import annotations

from typing import Any

ELIGIBLE_STATUS = "retraining_eligible"
NOT_ELIGIBLE_STATUS = "not_eligible"


def _metric_value(
    metrics: dict[str, Any],
    key: str,
) -> float | None:
    value = metrics.get(key)

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def evaluate_retraining_eligibility(
    *,
    model: dict[str, Any],
    performance: dict[str, Any],
    drift: dict[str, Any],
    data_quality: dict[str, Any],
    service: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert Phase 5 monitoring evidence into an explicit
    retraining eligibility decision.

    Retraining eligibility is evidence-based. Drift alone does not
    trigger retraining, and eligibility does not perform training.
    """

    model_name = str(model.get("name") or "unknown")
    model_version = str(model.get("version") or "unknown")
    serving_mode = str(model.get("serving_mode") or "unknown")

    sample_count = int(
        performance.get("sample_count") or 0
    )
    minimum_sample_count = int(
        performance.get("minimum_sample_count") or 0
    )

    sufficient_samples = (
        sample_count >= minimum_sample_count > 0
    )

    degradation = performance.get("degradation") or {}

    sustained_degradation = bool(
        degradation.get("sustained_degradation")
    )

    performance_comparison = (
        performance.get("comparison") or {}
    )

    model_nmae = _metric_value(
        performance_comparison,
        "model_nmae",
    )
    persistence_nmae = _metric_value(
        performance_comparison,
        "baseline_nmae",
    )

    beats_persistence = performance_comparison.get(
        "beats_baseline"
    )

    if beats_persistence is None:
        if (
            model_nmae is not None
            and persistence_nmae is not None
        ):
            beats_persistence = (
                model_nmae < persistence_nmae
            )
        else:
            beats_persistence = None

    baseline_comparison_available = (
        model_nmae is not None
        and persistence_nmae is not None
    )

    drift_status = str(
        drift.get("status") or "unknown"
    )

    data_quality_status = str(
        data_quality.get("status") or "unknown"
    )

    service_status = str(
        service.get("status") or "unknown"
    )

    data_quality_critical = (
        data_quality_status == "critical"
    )

    service_ready = service_status in {
        "ready",
        "healthy",
        "ok",
    }

    reasons: list[str] = []
    blocking_reasons: list[str] = []

    if not sufficient_samples:
        blocking_reasons.append(
            "Insufficient completed performance observations."
        )

    if not sustained_degradation:
        blocking_reasons.append(
            "Sustained performance degradation was not detected."
        )

    if not baseline_comparison_available:
        blocking_reasons.append(
            "Model and persistence baseline performance "
            "cannot be compared."
        )
    elif beats_persistence:
        blocking_reasons.append(
            "The learned model still outperforms the "
            "persistence baseline."
        )
    else:
        reasons.append(
            "The learned model underperforms the "
            "persistence baseline."
        )

    if data_quality_critical:
        blocking_reasons.append(
            "Data quality is critical."
        )
    else:
        reasons.append(
            f"Data quality status is {data_quality_status}."
        )

    if not service_ready:
        blocking_reasons.append(
            "The model service is not in a ready/healthy state."
        )
    else:
        reasons.append(
            "Model service is ready."
        )

    if drift_status in {"warning", "critical"}:
        reasons.append(
            f"Supporting feature drift signal: {drift_status}."
        )
    elif drift_status == "healthy":
        reasons.append(
            "No significant feature drift signal was detected."
        )
    else:
        reasons.append(
            f"Drift evidence is {drift_status}."
        )

    eligible = (
        sufficient_samples
        and sustained_degradation
        and baseline_comparison_available
        and beats_persistence is False
        and not data_quality_critical
        and service_ready
    )

    if eligible:
        status = ELIGIBLE_STATUS
        reasons.insert(
            0,
            "Sufficient sustained evidence exists for "
            "controlled candidate retraining.",
        )
    else:
        status = NOT_ELIGIBLE_STATUS

    return {
        "retraining_eligible": eligible,
        "status": status,
        "model": {
            "name": model_name,
            "version": model_version,
            "serving_mode": serving_mode,
        },
        "evidence": {
            "sample_count": sample_count,
            "minimum_sample_count": minimum_sample_count,
            "sufficient_samples": sufficient_samples,
            "sustained_degradation": sustained_degradation,
            "beats_persistence": beats_persistence,
            "baseline_comparison_available": (
                baseline_comparison_available
            ),
            "drift_status": drift_status,
            "data_quality_status": data_quality_status,
            "service_status": service_status,
        },
        "metrics": {
            "current_model_nmae": model_nmae,
            "persistence_nmae": persistence_nmae,
        },
        "reasons": reasons,
        "blocking_reasons": blocking_reasons,
    }