from __future__ import annotations

import numpy as np

from apps.model_service.app.drift import (
    DRIFT_CRITICAL_PSI,
    calculate_psi,
)


def test_identical_distributions_have_negligible_psi():
    values = np.linspace(
        1.0,
        100.0,
        100,
    ).tolist()

    psi = calculate_psi(
        values,
        values,
    )

    assert psi < 0.01


def test_shifted_distribution_has_high_psi():
    reference = np.linspace(
        1.0,
        100.0,
        100,
    ).tolist()

    current = np.linspace(
        101.0,
        200.0,
        100,
    ).tolist()

    psi = calculate_psi(
        reference,
        current,
    )

    assert psi >= DRIFT_CRITICAL_PSI


def test_warning_and_critical_thresholds_are_distinct():
    from apps.model_service.app.drift import (
        _status_from_psi,
    )

    assert _status_from_psi(0.05) == "healthy"
    assert _status_from_psi(0.10) == "warning"
    assert _status_from_psi(0.20) == "warning"
    assert _status_from_psi(0.25) == "critical"
    assert _status_from_psi(1.0) == "critical"

def test_empty_reference_is_rejected():
    try:
        calculate_psi(
            [],
            [1.0, 2.0, 3.0],
        )
    except ValueError as exc:
        assert "Reference distribution is empty" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for empty reference."
        )


def test_empty_current_distribution_is_rejected():
    try:
        calculate_psi(
            [1.0, 2.0, 3.0],
            [],
        )
    except ValueError as exc:
        assert "Current distribution is empty" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for empty current distribution."
        )