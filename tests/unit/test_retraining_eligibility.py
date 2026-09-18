from ml.lifecycle.eligibility import (
    ELIGIBLE_STATUS,
    NOT_ELIGIBLE_STATUS,
    evaluate_retraining_eligibility,
)


def _inputs() -> dict:
    return {
        "model": {
            "name": "building-energy-forecast",
            "version": "2",
            "serving_mode": "mlflow",
        },
        "performance": {
            "sample_count": 90,
            "minimum_sample_count": 30,
            "comparison": {
                "model_nmae": 0.12,
                "baseline_nmae": 0.10,
                "beats_baseline": False,
            },
            "degradation": {
                "sustained_degradation": True,
            },
        },
        "drift": {
            "status": "warning",
        },
        "data_quality": {
            "status": "healthy",
        },
        "service": {
            "status": "ready",
        },
    }


def test_eligible_when_all_required_evidence_is_present() -> None:
    result = evaluate_retraining_eligibility(
        **_inputs()
    )

    assert result["retraining_eligible"] is True
    assert result["status"] == ELIGIBLE_STATUS
    assert result["evidence"]["sufficient_samples"] is True
    assert result["evidence"]["sustained_degradation"] is True
    assert result["evidence"]["beats_persistence"] is False
    assert result["blocking_reasons"] == []


def test_insufficient_data_blocks_retraining() -> None:
    inputs = _inputs()
    inputs["performance"]["sample_count"] = 20

    result = evaluate_retraining_eligibility(
        **inputs
    )

    assert result["retraining_eligible"] is False
    assert result["status"] == NOT_ELIGIBLE_STATUS
    assert (
        "Insufficient completed performance observations."
        in result["blocking_reasons"]
    )


def test_healthy_performance_blocks_retraining() -> None:
    inputs = _inputs()
    inputs["performance"]["degradation"][
        "sustained_degradation"
    ] = False

    result = evaluate_retraining_eligibility(
        **inputs
    )

    assert result["retraining_eligible"] is False
    assert (
        "Sustained performance degradation was not detected."
        in result["blocking_reasons"]
    )


def test_baseline_beating_model_blocks_retraining() -> None:
    inputs = _inputs()
    inputs["performance"]["comparison"][
        "model_nmae"
    ] = 0.08
    inputs["performance"]["comparison"][
        "beats_baseline"
    ] = True

    result = evaluate_retraining_eligibility(
        **inputs
    )

    assert result["retraining_eligible"] is False
    assert (
        "The learned model still outperforms the "
        "persistence baseline."
        in result["blocking_reasons"]
    )


def test_critical_data_quality_blocks_retraining() -> None:
    inputs = _inputs()
    inputs["data_quality"]["status"] = "critical"

    result = evaluate_retraining_eligibility(
        **inputs
    )

    assert result["retraining_eligible"] is False
    assert (
        "Data quality is critical."
        in result["blocking_reasons"]
    )


def test_unhealthy_service_blocks_retraining() -> None:
    inputs = _inputs()
    inputs["service"]["status"] = "not_ready"

    result = evaluate_retraining_eligibility(
        **inputs
    )

    assert result["retraining_eligible"] is False
    assert (
        "The model service is not in a ready/healthy state."
        in result["blocking_reasons"]
    )


def test_drift_alone_does_not_make_model_eligible() -> None:
    inputs = _inputs()
    inputs["performance"]["degradation"][
        "sustained_degradation"
    ] = False
    inputs["drift"]["status"] = "critical"

    result = evaluate_retraining_eligibility(
        **inputs
    )

    assert result["retraining_eligible"] is False
    assert result["evidence"]["drift_status"] == "critical"


def test_degradation_without_baseline_failure_blocks() -> None:
    inputs = _inputs()
    inputs["performance"]["comparison"][
        "model_nmae"
    ] = 0.08
    inputs["performance"]["comparison"][
        "baseline_nmae"
    ] = 0.10
    inputs["performance"]["comparison"][
        "beats_baseline"
    ] = True

    result = evaluate_retraining_eligibility(
        **inputs
    )

    assert result["retraining_eligible"] is False


def test_missing_baseline_metrics_blocks() -> None:
    inputs = _inputs()
    inputs["performance"]["comparison"] = {
        "model_nmae": None,
        "baseline_nmae": None,
        "beats_baseline": None,
    }

    result = evaluate_retraining_eligibility(
        **inputs
    )

    assert result["retraining_eligible"] is False
    assert (
        "Model and persistence baseline performance "
        "cannot be compared."
        in result["blocking_reasons"]
    )


def test_baseline_serving_mode_does_not_fake_learned_model_evidence() -> None:
    inputs = _inputs()
    inputs["model"]["serving_mode"] = "baseline"

    result = evaluate_retraining_eligibility(
        **inputs
    )

    assert result["retraining_eligible"] is True
    assert result["model"]["serving_mode"] == "baseline"