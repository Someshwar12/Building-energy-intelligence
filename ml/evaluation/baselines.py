from __future__ import annotations

import pandas as pd


def add_baselines(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add legitimate forecasting baselines.

    Important:
    We calculate them on the COMPLETE chronological dataset first,
    then select the requested split. This prevents the validation/test
    boundary from destroying historical context.
    """

    result = (
        df
        .sort_values(["building_id", "timestamp"])
        .copy()
    )

    grouped = result.groupby(
        "building_id",
        sort=False,
    )["energy_kwh"]

    # At time t, predict t+1 using the current observation y_t.
    result["pred_persistence"] = grouped.shift(0)

    # Previous day.
    result["pred_previous_day"] = grouped.shift(24)

    # Previous week.
    result["pred_previous_week"] = grouped.shift(168)

    return result