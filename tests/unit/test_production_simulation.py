from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.simulate_production_data import (
    apply_normal_scenario,
    apply_shifted_scenario,
)


def _data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "building_id": [
                "building_a",
                "building_a",
                "building_b",
                "building_b",
            ],
            "timestamp": pd.date_range(
                "2017-12-31 20:00:00",
                periods=4,
                freq="h",
            ),
            "air_temperature": [
                10.0,
                11.0,
                12.0,
                13.0,
            ],
            "dew_temperature": [
                5.0,
                6.0,
                7.0,
                8.0,
            ],
            "wind_speed": [
                2.0,
                3.0,
                4.0,
                5.0,
            ],
            "target_next_hour_kwh": [
                100.0,
                110.0,
                120.0,
                130.0,
            ],
        }
    )


def test_normal_scenario_preserves_target_scale() -> None:
    data = _data()

    result = apply_normal_scenario(
        data,
        np.random.default_rng(42),
    )

    assert result["simulation_mode"].eq(
        "normal"
    ).all()

    assert result[
        "target_next_hour_kwh"
    ].equals(
        data["target_next_hour_kwh"]
    )


def test_shifted_scenario_changes_temperature() -> None:
    data = _data()

    result = apply_shifted_scenario(
        data,
        np.random.default_rng(42),
    )

    assert result["simulation_mode"].eq(
        "shifted"
    ).all()

    pd.testing.assert_series_equal(
        result["air_temperature"],
        data["air_temperature"] + 5.0,
        check_names=False,
    )

    pd.testing.assert_series_equal(
        result["dew_temperature"],
        data["dew_temperature"] + 3.0,
        check_names=False,
    )


def test_shifted_scenario_increases_target_distribution() -> None:
    data = _data()

    result = apply_shifted_scenario(
        data,
        np.random.default_rng(42),
    )

    assert (
        result["target_next_hour_kwh"].mean()
        > data["target_next_hour_kwh"].mean()
    )


def test_shifted_scenario_is_deterministic() -> None:
    data = _data()

    first = apply_shifted_scenario(
        data,
        np.random.default_rng(42),
    )

    second = apply_shifted_scenario(
        data,
        np.random.default_rng(42),
    )

    pd.testing.assert_frame_equal(
        first,
        second,
    )


def test_normal_scenario_is_deterministic() -> None:
    data = _data()

    first = apply_normal_scenario(
        data,
        np.random.default_rng(42),
    )

    second = apply_normal_scenario(
        data,
        np.random.default_rng(42),
    )

    pd.testing.assert_frame_equal(
        first,
        second,
    )


def test_shifted_scenario_does_not_modify_input() -> None:
    data = _data()
    original = data.copy(deep=True)

    apply_shifted_scenario(
        data,
        np.random.default_rng(42),
    )

    pd.testing.assert_frame_equal(
        data,
        original,
    )


def test_normal_scenario_does_not_modify_input() -> None:
    data = _data()
    original = data.copy(deep=True)

    apply_normal_scenario(
        data,
        np.random.default_rng(42),
    )

    pd.testing.assert_frame_equal(
        data,
        original,
    )