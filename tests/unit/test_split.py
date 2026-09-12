import pandas as pd

from ml.evaluation.split import (
    temporal_split,
)


def test_temporal_split_preserves_order():
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2020-01-01",
                periods=9,
                freq="h",
            ),
            "building_id": ["A"] * 9,
            "target_next_hour_kwh": range(9),
        }
    )

    result = temporal_split(
        df,
        train_start="2020-01-01 00:00:00",
        train_end="2020-01-01 02:00:00",
        validation_start="2020-01-01 03:00:00",
        validation_end="2020-01-01 05:00:00",
        test_start="2020-01-01 06:00:00",
        test_end="2020-01-01 08:00:00",
    )

    assert (
        result["train"]["timestamp"].max()
        < result["validation"]["timestamp"].min()
    )

    assert (
        result["validation"]["timestamp"].max()
        < result["test"]["timestamp"].min()
    )