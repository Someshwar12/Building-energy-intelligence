from __future__ import annotations

import numpy as np
import pandas as pd


def _valid_arrays(
    y_true,
    y_pred,
) -> tuple[np.ndarray, np.ndarray]:
    true = np.asarray(y_true, dtype=float)
    pred = np.asarray(y_pred, dtype=float)

    mask = (
        np.isfinite(true)
        & np.isfinite(pred)
    )

    return true[mask], pred[mask]


def mae(
    y_true,
    y_pred,
) -> float:
    true, pred = _valid_arrays(
        y_true,
        y_pred,
    )

    if len(true) == 0:
        return float("nan")

    return float(
        np.mean(np.abs(true - pred))
    )


def rmse(
    y_true,
    y_pred,
) -> float:
    true, pred = _valid_arrays(
        y_true,
        y_pred,
    )

    if len(true) == 0:
        return float("nan")

    return float(
        np.sqrt(
            np.mean(
                (true - pred) ** 2
            )
        )
    )


def cvrmse_pct(
    y_true,
    y_pred,
) -> float:
    true, _ = _valid_arrays(
        y_true,
        y_pred,
    )

    if len(true) == 0:
        return float("nan")

    mean_actual = float(
        np.mean(true)
    )

    if mean_actual == 0:
        return float("nan")

    return float(
        rmse(y_true, y_pred)
        / mean_actual
        * 100.0
    )


def nmae(
    y_true,
    y_pred,
) -> float:
    true, _ = _valid_arrays(
        y_true,
        y_pred,
    )

    if len(true) == 0:
        return float("nan")

    mean_actual = float(
        np.mean(true)
    )

    if mean_actual == 0:
        return float("nan")

    return float(
        mae(y_true, y_pred)
        / mean_actual
    )


def macro_building_nmae(
    df: pd.DataFrame,
    target: str,
    prediction: str,
) -> float:
    building_scores: list[float] = []

    for _, group in df.groupby(
        "building_id"
    ):
        if group[target].notna().sum() == 0:
            continue

        score = nmae(
            group[target],
            group[prediction],
        )

        if np.isfinite(score):
            building_scores.append(score)

    if not building_scores:
        return float("nan")

    return float(
        np.mean(building_scores)
    )


def evaluate(
    df: pd.DataFrame,
    target: str,
    prediction: str,
) -> dict[str, float]:
    mask = (
        df[target].notna()
        & df[prediction].notna()
    )

    subset = df.loc[mask]

    return {
        "mae": mae(
            subset[target],
            subset[prediction],
        ),
        "rmse": rmse(
            subset[target],
            subset[prediction],
        ),
        "cvrmse_pct": cvrmse_pct(
            subset[target],
            subset[prediction],
        ),
        "nmae": nmae(
            subset[target],
            subset[prediction],
        ),
        "macro_building_nmae": macro_building_nmae(
            subset,
            target,
            prediction,
        ),
    }


def per_building(
    df: pd.DataFrame,
    target: str,
    prediction: str,
) -> pd.DataFrame:
    rows: list[dict] = []

    for building_id, group in df.groupby(
        "building_id"
    ):
        rows.append(
            {
                "building_id": building_id,
                **evaluate(
                    group,
                    target,
                    prediction,
                ),
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            "macro_building_nmae"
        )
        .reset_index(drop=True)
    )