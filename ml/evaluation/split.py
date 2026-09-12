from __future__ import annotations

import pandas as pd


def temporal_split(
    df: pd.DataFrame,
    train_start: str,
    train_end: str,
    validation_start: str,
    validation_end: str,
    test_start: str,
    test_end: str,
) -> dict[str, pd.DataFrame]:
    result = df.copy()

    result["timestamp"] = pd.to_datetime(
        result["timestamp"]
    )

    train = result[
        result["timestamp"].between(
            pd.Timestamp(train_start),
            pd.Timestamp(train_end),
        )
    ].copy()

    validation = result[
        result["timestamp"].between(
            pd.Timestamp(validation_start),
            pd.Timestamp(validation_end),
        )
    ].copy()

    test = result[
        result["timestamp"].between(
            pd.Timestamp(test_start),
            pd.Timestamp(test_end),
        )
    ].copy()

    if train.empty:
        raise ValueError("Training split is empty.")

    if validation.empty:
        raise ValueError("Validation split is empty.")

    if test.empty:
        raise ValueError("Test split is empty.")

    if not (
        train["timestamp"].max()
        < validation["timestamp"].min()
    ):
        raise AssertionError(
            "Train and validation periods overlap."
        )

    if not (
        validation["timestamp"].max()
        < test["timestamp"].min()
    ):
        raise AssertionError(
            "Validation and test periods overlap."
        )

    return {
        "train": train,
        "validation": validation,
        "test": test,
    }