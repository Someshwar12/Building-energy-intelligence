from __future__ import annotations

from pathlib import Path
import sys
import time

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.ingestion.loaders import (  # noqa: E402
    find_first_existing,
    load_electricity,
    load_metadata,
    load_weather,
)
from ml.validation.data_quality import (  # noqa: E402
    add_quality_flags,
    coverage_report,
    required_columns,
    validate_duplicate_keys,
    validate_energy_values,
    validate_timestamps,
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


def file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def report_dataframe(
    name: str,
    df: pd.DataFrame,
) -> None:
    print(f"\n{'=' * 70}")
    print(name)
    print(f"{'=' * 70}")

    print(f"Rows       : {len(df):,}")
    print(f"Columns    : {len(df.columns):,}")
    print(
        f"Memory     : "
        f"{df.memory_usage(deep=True).sum() / (1024 ** 2):,.2f} MB"
    )

    print("\nColumns:")
    for column in df.columns:
        print(
            f"  {column:<30}"
            f"{str(df[column].dtype):<15}"
        )


def main() -> None:
    started = time.perf_counter()

    print("BUILDING & ENERGY INTELLIGENCE PLATFORM")
    print("PHASE 0 — DATA FEASIBILITY PROOF")
    print()

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

    print("Dataset files:")
    print(
        f"  Electricity : {electricity_path}"
        f" ({file_size_mb(electricity_path):,.2f} MB)"
    )
    print(
        f"  Metadata    : {metadata_path}"
        f" ({file_size_mb(metadata_path):,.2f} MB)"
    )
    print(
        f"  Weather     : {weather_path}"
        f" ({file_size_mb(weather_path):,.2f} MB)"
    )

    load_started = time.perf_counter()

    electricity = load_electricity(
        electricity_path
    )

    metadata = load_metadata(
        metadata_path
    )

    weather = load_weather(
        weather_path
    )

    load_elapsed = time.perf_counter() - load_started

    print(
        f"\nLoad time: {load_elapsed:,.2f} seconds"
    )

    report_dataframe(
        "ELECTRICITY",
        electricity,
    )

    report_dataframe(
        "METADATA",
        metadata,
    )

    report_dataframe(
        "WEATHER",
        weather,
    )

    print("\nElectricity date range:")

    electricity_timestamps = pd.to_datetime(
        electricity["timestamp"],
        errors="coerce",
    )

    print(
        f"  {electricity_timestamps.min()}"
        f" → "
        f"{electricity_timestamps.max()}"
    )

    print("\nBuildings:")
    print(
        f"  electricity buildings:"
        f" {electricity['building_id'].nunique():,}"
    )
    print(
        f"  metadata buildings:"
        f" {metadata['building_id'].nunique():,}"
    )

    print("\nValidation checks:")

    errors: list[str] = []

    errors += required_columns(
        electricity,
        {
            "timestamp",
            "building_id",
            "energy_kwh",
        },
        "electricity",
    )

    errors += required_columns(
        metadata,
        {
            "building_id",
        },
        "metadata",
    )

    errors += required_columns(
        weather,
        {
            "timestamp",
            "site_id",
        },
        "weather",
    )

    errors += validate_timestamps(
        electricity,
        "electricity",
    )

    errors += validate_timestamps(
        weather,
        "weather",
    )

    errors += validate_energy_values(
        electricity,
    )

    errors += validate_duplicate_keys(
        electricity,
    )

    if errors:
        print("\nVALIDATION PROBLEMS:")
        for error in errors:
            print(f"  [FAIL] {error}")
    else:
        print("  [PASS] Required schema")
        print("  [PASS] Timestamp parsing")
        print("  [PASS] Energy-value validation")
        print("  [PASS] Duplicate-key validation")

    electricity = add_quality_flags(
        electricity
    )

    print("\nQuality flag distribution:")

    quality_counts = (
        electricity["quality_flag"]
        .value_counts(dropna=False)
    )

    for flag, count in quality_counts.items():
        percentage = (
            count / len(electricity) * 100
        )

        print(
            f"  {str(flag):<20}"
            f"{count:>12,}"
            f" ({percentage:>6.2f}%)"
        )

    print("\nCoverage report:")

    coverage = coverage_report(
        electricity,
        start="2016-01-01 00:00:00",
        end="2017-12-31 23:00:00",
        frequency="h",
    )

    print(
        coverage.head(20).to_string(
            index=False
        )
    )

    reports_dir = ROOT / "reports" / "generated"
    reports_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    coverage.to_csv(
        reports_dir / "phase0_building_coverage.csv",
        index=False,
    )

    quality_counts.rename(
        "count"
    ).to_csv(
        reports_dir / "phase0_quality_flags.csv"
    )

    elapsed = time.perf_counter() - started

    print("\n" + "=" * 70)
    print("PHASE 0 SUMMARY")
    print("=" * 70)

    print(
        f"Total execution time: "
        f"{elapsed:,.2f} seconds"
    )

    print(
        f"Electricity rows: "
        f"{len(electricity):,}"
    )

    print(
        f"Unique buildings: "
        f"{electricity['building_id'].nunique():,}"
    )

    if errors:
        print("\nRESULT: DATA PROOF NEEDS INVESTIGATION")
        raise SystemExit(1)

    print("\nRESULT: DATA LOADED AND BASIC VALIDATION PASSED")


if __name__ == "__main__":
    main()