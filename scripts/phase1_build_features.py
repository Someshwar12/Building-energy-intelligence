from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.config import phase1_config  # noqa: E402
from ml.ingestion.loaders import (  # noqa: E402
    find_first_existing,
    load_electricity,
    load_metadata,
    load_weather,
)
from ml.validation.data_quality import (  # noqa: E402
    add_quality_flags,
    coverage_report,
)
from ml.features.build import (  # noqa: E402
    merge_energy_metadata_weather,
    build_features,
)


ELECTRICITY_CANDIDATES = [
    "data/raw/bdg2/electricity_cleaned.csv",
]

METADATA_CANDIDATES = [
    "data/raw/bdg2/metadata.csv",
]

WEATHER_CANDIDATES = [
    "data/raw/bdg2/weather.csv",
]


def select_buildings(
    coverage: pd.DataFrame,
    n_buildings: int,
    min_coverage_ratio: float,
    max_missing_ratio: float,
) -> list[str]:
    eligible = coverage[
        (coverage["coverage_ratio"] >= min_coverage_ratio)
        & (coverage["missing_ratio"] <= max_missing_ratio)
        & (coverage["negative_values"] == 0)
    ].copy()

    if len(eligible) < n_buildings:
        raise RuntimeError(
            f"Only {len(eligible)} buildings pass the "
            f"quality thresholds. Need {n_buildings}."
        )

    selected = (
        eligible
        .sort_values(
            [
                "coverage_ratio",
                "missing_ratio",
                "building_id",
            ],
            ascending=[
                False,
                True,
                True,
            ],
        )
        .head(n_buildings)
        ["building_id"]
        .astype(str)
        .tolist()
    )

    return selected


def main() -> None:
    cfg = phase1_config(
        ROOT / "configs/project.yaml"
    )

    electricity_path = find_first_existing(
        ELECTRICITY_CANDIDATES,
        ROOT,
    )

    metadata_path = find_first_existing(
        METADATA_CANDIDATES,
        ROOT,
    )

    weather_path = find_first_existing(
        WEATHER_CANDIDATES,
        ROOT,
    )

    electricity = add_quality_flags(
        load_electricity(
            electricity_path
        )
    )

    metadata = load_metadata(
        metadata_path
    )

    weather = load_weather(
        weather_path
    )

    coverage = coverage_report(
        electricity,
        start=cfg.train_start,
        end=cfg.test_end,
        frequency=cfg.frequency,
    )

    selected_buildings = select_buildings(
        coverage,
        cfg.n_buildings,
        cfg.min_coverage_ratio,
        cfg.max_missing_ratio,
    )

    print("Selected buildings:")

    for building_id in selected_buildings:
        print(f"  - {building_id}")

    electricity = electricity[
        electricity["building_id"]
        .astype(str)
        .isin(selected_buildings)
    ].copy()

    metadata = metadata[
        metadata["building_id"]
        .astype(str)
        .isin(selected_buildings)
    ].copy()

    base = merge_energy_metadata_weather(
        electricity,
        metadata,
        weather,
    )

    features = build_features(
        base,
        lags=cfg.lags,
        rolling_windows=cfg.rolling_windows,
        degree_day_base_c=cfg.degree_day_base_c,
        target_name=cfg.target_name,
    )

    cfg.processed_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    cfg.reports_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    features_path = (
        cfg.processed_root
        / "phase1_features.parquet"
    )

    selected_path = (
        cfg.processed_root
        / "selected_buildings.csv"
    )

    coverage_path = (
        cfg.reports_root
        / "phase1_building_coverage.csv"
    )

    features.to_parquet(
        features_path,
        index=False,
    )

    pd.DataFrame(
        {
            "building_id": selected_buildings
        }
    ).to_csv(
        selected_path,
        index=False,
    )

    coverage.to_csv(
        coverage_path,
        index=False,
    )

    print()
    print(
        f"Feature rows: {len(features):,}"
    )

    print(
        f"Feature columns: {len(features.columns):,}"
    )

    print(
        f"Saved: {features_path}"
    )


if __name__ == "__main__":
    main()