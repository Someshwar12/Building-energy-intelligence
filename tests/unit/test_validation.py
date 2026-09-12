import pandas as pd

from ml.validation.data_quality import (
    add_quality_flags,
)


def test_missing_and_negative_values_are_flagged():
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2020-01-01",
                periods=3,
                freq="h",
            ),
            "building_id": [
                "A",
                "A",
                "A",
            ],
            "energy_kwh": [
                100.0,
                -5.0,
                None,
            ],
        }
    )

    result = add_quality_flags(
        df
    )

    assert (
        result.loc[
            1,
            "quality_flag",
        ]
        == "INVALID_NEGATIVE"
    )

    assert (
        result.loc[
            2,
            "quality_flag",
        ]
        == "MISSING"
    )