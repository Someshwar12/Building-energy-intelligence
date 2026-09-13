from __future__ import annotations

import numpy as np
import pandas as pd


def merge_energy_metadata_weather(
    electricity: pd.DataFrame,
    metadata: pd.DataFrame,
    weather: pd.DataFrame,
) -> pd.DataFrame:
    energy = electricity.copy()

    energy["timestamp"] = pd.to_datetime(
        energy["timestamp"],
        errors="coerce",
    )

    energy["building_id"] = (
        energy["building_id"].astype(str)
    )

    # Normalize BDG2 metadata column names.
    meta = metadata.copy()

    metadata_rename = {
        "primaryspaceusage": "primary_use",
        "sqft": "square_feet",
        "sqm": "floor_area",
    }

    meta = meta.rename(
        columns={
            source: target
            for source, target in metadata_rename.items()
            if source in meta.columns
        }
    )

    meta["building_id"] = (
        meta["building_id"].astype(str)
    )

    metadata_columns = [
        column
        for column in [
            "building_id",
            "site_id",
            "primary_use",
            "square_feet",
            "floor_area",
            "timezone",
        ]
        if column in meta.columns
    ]

    meta = (
        meta[metadata_columns]
        .drop_duplicates(subset=["building_id"])
    )

    result = energy.merge(
        meta,
        on="building_id",
        how="left",
        validate="many_to_one",
    )

    # Normalize BDG2 weather column names.
    weather_df = weather.copy()

    weather_rename = {
        "airTemperature": "air_temperature",
        "dewTemperature": "dew_temperature",
        "cloudCoverage": "cloud_coverage",
        "windSpeed": "wind_speed",
        "windDirection": "wind_direction",
        "seaLvlPressure": "sea_level_pressure",
        "precipDepth1HR": "precip_depth_1_hr",
    }

    weather_df = weather_df.rename(
        columns={
            source: target
            for source, target in weather_rename.items()
            if source in weather_df.columns
        }
    )

    weather_df["timestamp"] = pd.to_datetime(
        weather_df["timestamp"],
        errors="coerce",
    )

    weather_df["site_id"] = (
        weather_df["site_id"].astype(str)
    )

    weather_columns = [
        column
        for column in [
            "timestamp",
            "site_id",
            "air_temperature",
            "dew_temperature",
            "cloud_coverage",
            "wind_speed",
            "wind_direction",
            "sea_level_pressure",
            "precip_depth_1_hr",
        ]
        if column in weather_df.columns
    ]

    weather_df = weather_df[weather_columns]

    if "site_id" in result.columns:
        result["site_id"] = result["site_id"].astype(str)

        result = result.merge(
            weather_df,
            on=["site_id", "timestamp"],
            how="left",
            validate="many_to_one",
        )

    return (
        result
        .sort_values(["building_id", "timestamp"])
        .reset_index(drop=True)
    )


def add_calendar_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    result = df.copy()

    timestamp = pd.to_datetime(
        result["timestamp"]
    )

    result["hour"] = timestamp.dt.hour
    result["day_of_week"] = timestamp.dt.dayofweek
    result["month"] = timestamp.dt.month
    result["day_of_year"] = timestamp.dt.dayofyear

    result["is_weekend"] = (
        timestamp.dt.dayofweek.isin([5, 6])
        .astype(int)
    )

    result["hour_sin"] = np.sin(
        2 * np.pi * result["hour"] / 24.0
    )

    result["hour_cos"] = np.cos(
        2 * np.pi * result["hour"] / 24.0
    )

    result["day_of_year_sin"] = np.sin(
        2 * np.pi * result["day_of_year"] / 365.25
    )

    result["day_of_year_cos"] = np.cos(
        2 * np.pi * result["day_of_year"] / 365.25
    )

    return result


def add_lags_and_rollings(
    df: pd.DataFrame,
    lags: tuple[int, ...],
    rolling_windows: tuple[int, ...],
) -> pd.DataFrame:
    result = (
        df
        .sort_values(["building_id", "timestamp"])
        .copy()
    )

    grouped = result.groupby(
        "building_id",
        sort=False,
    )["energy_kwh"]

    for lag in lags:
        result[f"energy_lag_{lag}h"] = (
            grouped.shift(lag)
        )

    # STRICTLY PAST data.
    #
    # The shift(1) is deliberate:
    # rolling features at time t can use t-1, t-2, ...
    # but must not include the current/future target interval.
    past_energy = grouped.shift(1)

    for window in rolling_windows:
        result[
            f"energy_roll_mean_{window}h"
        ] = (
            past_energy
            .groupby(result["building_id"])
            .transform(
                lambda series, window=window: series.rolling(
                    window=window,
                    min_periods=max(1, window // 2),
                ).mean()
            )
        )

        if window in (24, 168):
            result[
                f"energy_roll_max_{window}h"
            ] = (
                past_energy
                .groupby(result["building_id"])
                .transform(
                    lambda series, window=window: series.rolling(
                        window=window,
                        min_periods=max(1, window // 2),
                    ).max()
                )
            )

    return result


def add_weather_features(
    df: pd.DataFrame,
    base_c: float,
) -> pd.DataFrame:
    result = df.copy()

    if "air_temperature" in result.columns:
        temperature = pd.to_numeric(
            result["air_temperature"],
            errors="coerce",
        )

        result["heating_degree_hour"] = (
            base_c - temperature
        ).clip(lower=0)

        result["cooling_degree_hour"] = (
            temperature - base_c
        ).clip(lower=0)

    return result


def add_target(
    df: pd.DataFrame,
    target_name: str,
) -> pd.DataFrame:
    result = (
        df
        .sort_values(["building_id", "timestamp"])
        .copy()
    )

    result[target_name] = (
        result
        .groupby("building_id", sort=False)["energy_kwh"]
        .shift(-1)
    )

    return result


def build_features(
    df: pd.DataFrame,
    lags: tuple[int, ...],
    rolling_windows: tuple[int, ...],
    degree_day_base_c: float,
    target_name: str,
) -> pd.DataFrame:
    result = add_calendar_features(df)

    result = add_lags_and_rollings(
        result,
        lags=lags,
        rolling_windows=rolling_windows,
    )

    result = add_weather_features(
        result,
        base_c=degree_day_base_c,
    )

    result = add_target(
        result,
        target_name=target_name,
    )

    return result