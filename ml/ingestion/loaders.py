from __future__ import annotations

from pathlib import Path

import pandas as pd


def find_first_existing(
    candidates: list[str],
    project_root: Path,
) -> Path:
    checked: list[str] = []

    for candidate in candidates:
        path = project_root / candidate
        checked.append(str(path))

        if path.exists():
            return path

    raise FileNotFoundError(
        "Could not find any expected dataset file.\n\n"
        "Checked:\n"
        + "\n".join(f"  - {item}" for item in checked)
    )


def load_csv(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")

    return pd.read_csv(path, **kwargs)


def load_electricity(path: Path) -> pd.DataFrame:
    """
    Load BDG2 electricity data and normalize it into long format:

        timestamp | building_id | energy_kwh

    BDG2 cleaned electricity is commonly represented as:
        timestamp + one column per building.
    """

    df = load_csv(path)

    if df.empty:
        raise ValueError(f"Electricity dataset is empty: {path}")

    # Normalize timestamp column.
    if "timestamp" not in df.columns:
        first_column = df.columns[0]
        df = df.rename(columns={first_column: "timestamp"})

    # Already-long possibility.
    if {"building_id", "meter_reading"}.issubset(df.columns):
        return (
            df.rename(columns={"meter_reading": "energy_kwh"})
            [["timestamp", "building_id", "energy_kwh"]]
            .copy()
        )

    if {"building_id", "electricity"}.issubset(df.columns):
        return (
            df.rename(columns={"electricity": "energy_kwh"})
            [["timestamp", "building_id", "energy_kwh"]]
            .copy()
        )

    # Expected wide BDG2 structure.
    building_columns = [
        column for column in df.columns
        if column != "timestamp"
    ]

    if not building_columns:
        raise ValueError(
            "No building columns found in electricity dataset."
        )

    long_df = df.melt(
        id_vars=["timestamp"],
        value_vars=building_columns,
        var_name="building_id",
        value_name="energy_kwh",
    )

    long_df["building_id"] = long_df["building_id"].astype(str)

    return long_df


def load_metadata(path: Path) -> pd.DataFrame:
    df = load_csv(path)

    if df.empty:
        raise ValueError(f"Metadata dataset is empty: {path}")

    if "building_id" not in df.columns:
        # Handle exports where the first column contains the building ID.
        df = df.rename(columns={df.columns[0]: "building_id"})

    df["building_id"] = df["building_id"].astype(str)

    return df


def load_weather(path: Path) -> pd.DataFrame:
    df = load_csv(path)

    if df.empty:
        raise ValueError(f"Weather dataset is empty: {path}")

    if "timestamp" not in df.columns:
        df = df.rename(columns={df.columns[0]: "timestamp"})

    if "site_id" not in df.columns:
        raise ValueError(
            "Weather dataset must contain a 'site_id' column."
        )

    df["site_id"] = df["site_id"].astype(str)

    return df