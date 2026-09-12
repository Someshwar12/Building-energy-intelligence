from __future__ import annotations

import numpy as np
import pandas as pd


def residual_table(
    df: pd.DataFrame,
    target: str,
    prediction: str,
) -> pd.DataFrame:
    result = df.copy()

    result["residual"] = (
        result[target]
        - result[prediction]
    )

    result["absolute_error"] = (
        result["residual"].abs()
    )

    timestamps = pd.to_datetime(
        result["timestamp"]
    )

    result["hour"] = timestamps.dt.hour

    result["day_of_week"] = (
        timestamps.dt.dayofweek
    )

    result["weekpart"] = np.where(
        timestamps.dt.dayofweek < 5,
        "weekday",
        "weekend",
    )

    result["month"] = timestamps.dt.month

    return result


def grouped_error(
    residuals: pd.DataFrame,
    group_column: str,
) -> pd.DataFrame:
    subset = residuals.dropna(
        subset=[
            "residual",
            "absolute_error",
        ]
    )

    return (
        subset
        .groupby(group_column)
        .agg(
            observations=(
                "residual",
                "size",
            ),
            mean_error=(
                "residual",
                "mean",
            ),
            mae=(
                "absolute_error",
                "mean",
            ),
            rmse=(
                "residual",
                lambda values: float(
                    np.sqrt(
                        np.mean(
                            np.square(
                                values
                            )
                        )
                    )
                ),
            ),
        )
        .reset_index()
    )