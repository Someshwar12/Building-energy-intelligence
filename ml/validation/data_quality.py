from __future__ import annotations

import pandas as pd


def required_columns(
    df: pd.DataFrame,
    required: set[str],
    dataset_name: str,
) -> list[str]:
    missing = sorted(required - set(df.columns))

    if not missing:
        return []

    return [
        f"{dataset_name}: missing required columns: {missing}"
    ]


def validate_timestamps(
    df: pd.DataFrame,
    dataset_name: str,
) -> list[str]:
    if "timestamp" not in df.columns:
        return [
            f"{dataset_name}: timestamp column missing"
        ]

    timestamps = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    invalid_count = int(timestamps.isna().sum())

    if invalid_count == 0:
        return []

    return [
        f"{dataset_name}: {invalid_count} invalid timestamps"
    ]


def validate_energy_values(
    df: pd.DataFrame,
) -> list[str]:
    if "energy_kwh" not in df.columns:
        return ["electricity: energy_kwh column missing"]

    values = pd.to_numeric(
        df["energy_kwh"],
        errors="coerce",
    )

    negative_count = int((values < 0).sum())

    if negative_count == 0:
        return []

    return [
        f"electricity: {negative_count} negative energy observations"
    ]


def validate_duplicate_keys(
    df: pd.DataFrame,
) -> list[str]:
    required = {
        "building_id",
        "timestamp",
    }

    if not required.issubset(df.columns):
        return []

    duplicate_count = int(
        df.duplicated(
            subset=["building_id", "timestamp"],
            keep=False,
        ).sum()
    )

    if duplicate_count == 0:
        return []

    return [
        f"electricity: {duplicate_count} rows participate in duplicate "
        "building/timestamp keys"
    ]


def add_quality_flags(
    df: pd.DataFrame,
) -> pd.DataFrame:
    result = df.copy()

    result["timestamp"] = pd.to_datetime(
        result["timestamp"],
        errors="coerce",
    )

    result["energy_kwh"] = pd.to_numeric(
        result["energy_kwh"],
        errors="coerce",
    )

    result["quality_missing"] = (
        result["energy_kwh"].isna()
    )

    result["quality_negative"] = (
        result["energy_kwh"] < 0
    )

    result["quality_duplicate"] = (
        result.duplicated(
            subset=["building_id", "timestamp"],
            keep=False,
        )
    )

    result["quality_flag"] = "OK"

    result.loc[
        result["quality_missing"],
        "quality_flag",
    ] = "MISSING"

    result.loc[
        result["quality_negative"],
        "quality_flag",
    ] = "INVALID_NEGATIVE"

    result.loc[
        result["quality_duplicate"],
        "quality_flag",
    ] = "DUPLICATE"

    return result


def coverage_report(
    electricity: pd.DataFrame,
    start: str,
    end: str,
    frequency: str = "h",
) -> pd.DataFrame:
    """
    Measure observation coverage for each building.

    This is intentionally based on unique timestamps so duplicate rows do
    not artificially inflate coverage.
    """

    expected_index = pd.date_range(
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        freq=frequency,
    )

    expected_hours = len(expected_index)

    rows: list[dict] = []

    for building_id, group in electricity.groupby(
        "building_id",
        sort=True,
    ):
        timestamps = (
            pd.to_datetime(
                group["timestamp"],
                errors="coerce",
            )
            .dropna()
            .drop_duplicates()
        )

        timestamps = timestamps[
            timestamps.between(
                pd.Timestamp(start),
                pd.Timestamp(end),
            )
        ]

        observed_hours = len(timestamps)

        coverage_ratio = (
            observed_hours / expected_hours
            if expected_hours
            else 0.0
        )

        negative_values = int(
            (
                pd.to_numeric(
                    group["energy_kwh"],
                    errors="coerce",
                )
                < 0
            ).sum()
        )

        duplicate_rows = int(
            group.duplicated(
                subset=["timestamp"],
                keep=False,
            ).sum()
        )

        missing_values = int(
            pd.to_numeric(
                group["energy_kwh"],
                errors="coerce",
            ).isna().sum()
        )

        rows.append(
            {
                "building_id": str(building_id),
                "expected_hours": expected_hours,
                "observed_hours": observed_hours,
                "coverage_ratio": coverage_ratio,
                "missing_ratio": 1.0 - coverage_ratio,
                "missing_values": missing_values,
                "duplicate_rows": duplicate_rows,
                "negative_values": negative_values,
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "building_id",
                "expected_hours",
                "observed_hours",
                "coverage_ratio",
                "missing_ratio",
                "missing_values",
                "duplicate_rows",
                "negative_values",
            ]
        )

    return pd.DataFrame(rows).sort_values(
        ["coverage_ratio", "building_id"],
        ascending=[False, True],
    ).reset_index(drop=True)