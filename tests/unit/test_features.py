import pandas as pd

from ml.features.build import (
    add_lags_and_rollings,
    add_target,
)


def test_next_hour_target():
    df = pd.DataFrame(
        {
            "building_id": [
                "A",
                "A",
                "A",
            ],
            "timestamp": pd.date_range(
                "2020-01-01",
                periods=3,
                freq="h",
            ),
            "energy_kwh": [
                100.0,
                200.0,
                300.0,
            ],
        }
    )

    result = add_target(
        df,
        "target_next_hour_kwh",
    )

    assert (
        result.iloc[0][
            "target_next_hour_kwh"
        ]
        == 200.0
    )

    assert (
        result.iloc[1][
            "target_next_hour_kwh"
        ]
        == 300.0
    )

    assert pd.isna(
        result.iloc[2][
            "target_next_hour_kwh"
        ]
    )


def test_lag_contains_only_previous_values():
    df = pd.DataFrame(
        {
            "building_id": [
                "A",
                "A",
                "A",
            ],
            "timestamp": pd.date_range(
                "2020-01-01",
                periods=3,
                freq="h",
            ),
            "energy_kwh": [
                100.0,
                200.0,
                300.0,
            ],
        }
    )

    result = add_lags_and_rollings(
        df,
        lags=(1,),
        rolling_windows=(3,),
    )

    assert pd.isna(
        result.iloc[0][
            "energy_lag_1h"
        ]
    )

    assert (
        result.iloc[1][
            "energy_lag_1h"
        ]
        == 100.0
    )

    assert (
        result.iloc[2][
            "energy_lag_1h"
        ]
        == 200.0
    )