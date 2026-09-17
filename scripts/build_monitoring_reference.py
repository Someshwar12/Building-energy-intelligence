from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REFERENCE_FEATURES = [
    # Building characteristics
    "square_feet",
    "floor_area",

    # Weather
    "air_temperature",
    "dew_temperature",
    "cloud_coverage",
    "wind_speed",
    "wind_direction",
    "sea_level_pressure",
    "precip_depth_1_hr",

    # Temporal
    "hour",
    "day_of_week",
    "month",
    "day_of_year",
    "is_weekend",

    # Energy/history
    "energy_kwh",
    "energy_lag_1h",
    "energy_lag_2h",
    "energy_lag_3h",
    "energy_lag_24h",
    "energy_lag_48h",
    "energy_lag_72h",
    "energy_lag_168h",
    "energy_roll_mean_3h",
    "energy_roll_mean_6h",
    "energy_roll_mean_24h",
    "energy_roll_max_24h",
    "energy_roll_mean_168h",
    "energy_roll_max_168h",
    "heating_degree_hour",
    "cooling_degree_hour",
]

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phase1_features.parquet"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "configs"
    / "monitoring_reference.json"
)


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Feature dataset not found: {INPUT_PATH}"
        )

    frame = pd.read_parquet(INPUT_PATH)

    print(
        f"Loaded {len(frame):,} feature rows."
    )

    missing = [
        column
        for column in REFERENCE_FEATURES
        if column not in frame.columns
    ]

    if missing:
        raise ValueError(
            "Reference features are missing: "
            + ", ".join(missing)
        )

    profile = {
        "version": "1.0",
        "source": (
            "data/processed/"
            "phase1_features.parquet"
        ),
        "sample_count": len(frame),
        "features": {},
    }

    for feature in REFERENCE_FEATURES:
        values = (
            pd.to_numeric(
                frame[feature],
                errors="coerce",
            )
            .dropna()
            .to_numpy(dtype=float)
        )

        values = values[
            np.isfinite(values)
        ]

        if len(values) == 0:
            print(
                f"Skipping empty feature: {feature}"
            )
            continue

        profile["features"][feature] = {
            "sample_count": len(values),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "values": values.tolist(),
        }

        print(
            f"{feature}: "
            f"{len(values):,} reference samples"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            profile,
            file,
            indent=2,
        )

    print(
        f"\nSaved reference profile to: "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()