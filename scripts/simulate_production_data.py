from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FEATURES_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phase1_features.parquet"
)

OUTPUT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "production"
)

DEFAULT_SEED = 42

DEFAULT_BUILDINGS = [
    "Bear_assembly_Angel",
    "Bear_assembly_Beatrice",
    "Bear_assembly_Danial",
    "Bear_assembly_Diana",
    "Bear_assembly_Genia",
    "Bear_assembly_Harry",
    "Bear_assembly_Jose",
    "Bear_assembly_Roxy",
    "Bear_assembly_Ruby",
    "Bear_education_Alfredo",
    "Bear_education_Alvaro",
    "Bear_education_Arnold",
]

REQUIRED_COLUMNS = {
    "building_id",
    "timestamp",
    "air_temperature",
    "dew_temperature",
    "wind_speed",
    "target_next_hour_kwh",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic simulated production "
            "data from the existing BDG2 feature dataset."
        )
    )

    parser.add_argument(
        "--mode",
        choices=("normal", "shifted", "both"),
        default="both",
        help="Production scenario to generate.",
    )

    parser.add_argument(
        "--rows-per-building",
        type=int,
        default=168,
        help=(
            "Number of hourly observations to generate "
            "per building."
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Deterministic random seed.",
    )

    return parser.parse_args()


def validate_input(data: pd.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS - set(data.columns))

    if missing:
        raise ValueError(
            "phase1_features.parquet is missing required "
            f"columns: {', '.join(missing)}"
        )

    if data.empty:
        raise ValueError(
            "phase1_features.parquet contains no rows."
        )

    if data["building_id"].isna().any():
        raise ValueError(
            "building_id contains missing values."
        )

    if data["timestamp"].isna().any():
        raise ValueError(
            "timestamp contains missing values."
        )


def select_production_window(
    data: pd.DataFrame,
    rows_per_building: int,
) -> pd.DataFrame:
    selected_frames: list[pd.DataFrame] = []

    for building_id in DEFAULT_BUILDINGS:
        building = data[
            data["building_id"] == building_id
        ].copy()

        if building.empty:
            raise ValueError(
                f"Building not found in feature dataset: "
                f"{building_id}"
            )

        building = building.sort_values("timestamp")

        if len(building) < rows_per_building:
            raise ValueError(
                f"Building {building_id} has only "
                f"{len(building)} rows; "
                f"{rows_per_building} are required."
            )

        selected_frames.append(
            building.tail(rows_per_building)
        )

    result = pd.concat(
        selected_frames,
        ignore_index=True,
    )

    return result.sort_values(
        ["building_id", "timestamp"]
    ).reset_index(drop=True)


def apply_normal_scenario(
    data: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    result = data.copy()

    # Small deterministic measurement noise represents
    # ordinary production variability without creating
    # a distribution shift.
    for column, scale in (
        ("air_temperature", 0.05),
        ("dew_temperature", 0.05),
        ("wind_speed", 0.02),
    ):
        values = pd.to_numeric(
            result[column],
            errors="coerce",
        )

        noise = rng.normal(
            loc=0.0,
            scale=scale,
            size=len(result),
        )

        result[column] = values + noise

    result["simulation_mode"] = "normal"
    result["simulation_seed"] = int(rng.bit_generator._seed_seq.entropy)

    return result


def apply_shifted_scenario(
    data: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    result = data.copy()

    air_temperature = pd.to_numeric(
        result["air_temperature"],
        errors="coerce",
    )

    dew_temperature = pd.to_numeric(
        result["dew_temperature"],
        errors="coerce",
    )

    wind_speed = pd.to_numeric(
        result["wind_speed"],
        errors="coerce",
    )

    target = pd.to_numeric(
        result["target_next_hour_kwh"],
        errors="coerce",
    )

    # Controlled covariate shift:
    # temperatures move upward and wind intensity changes.
    result["air_temperature"] = (
        air_temperature + 5.0
    )

    result["dew_temperature"] = (
        dew_temperature + 3.0
    )

    result["wind_speed"] = (
        wind_speed.fillna(0.0) * 1.5
    )

    # Controlled target shift:
    # actual consumption increases relative to the
    # historical relationship learned by the model.
    target_noise = rng.normal(
        loc=1.0,
        scale=0.02,
        size=len(result),
    )

    result["target_next_hour_kwh"] = (
        target * 1.25 * target_noise
    )

    result["simulation_mode"] = "shifted"
    result["simulation_seed"] = int(rng.bit_generator._seed_seq.entropy)

    return result


def scenario_summary(
    data: pd.DataFrame,
) -> dict[str, float | int | str]:
    return {
        "mode": str(data["simulation_mode"].iloc[0]),
        "rows": len(data),
        "buildings": int(
            data["building_id"].nunique()
        ),
        "air_temperature_mean": float(
            data["air_temperature"].mean()
        ),
        "dew_temperature_mean": float(
            data["dew_temperature"].mean()
        ),
        "wind_speed_mean": float(
            data["wind_speed"].mean()
        ),
        "target_next_hour_kwh_mean": float(
            data["target_next_hour_kwh"].mean()
        ),
    }


def save_scenario(
    data: pd.DataFrame,
    mode: str,
) -> Path:
    output_path = (
        OUTPUT_ROOT
        / f"{mode}_production.parquet"
    )

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_parquet(
        output_path,
        index=False,
    )

    return output_path


def generate_scenario(
    base_data: pd.DataFrame,
    mode: str,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    if mode == "normal":
        return apply_normal_scenario(
            base_data,
            rng,
        )

    if mode == "shifted":
        return apply_shifted_scenario(
            base_data,
            rng,
        )

    raise ValueError(
        f"Unsupported scenario mode: {mode}"
    )


def main() -> None:
    args = parse_args()

    if args.rows_per_building <= 0:
        raise ValueError(
            "--rows-per-building must be greater than zero."
        )

    if not FEATURES_PATH.exists():
        raise FileNotFoundError(
            "Feature dataset not found: "
            f"{FEATURES_PATH}"
        )

    data = pd.read_parquet(FEATURES_PATH)

    validate_input(data)

    base_data = select_production_window(
        data,
        rows_per_building=args.rows_per_building,
    )

    modes = (
        ("normal", "shifted")
        if args.mode == "both"
        else (args.mode,)
    )

    print(
        "Production simulation source:"
        f" {FEATURES_PATH}"
    )

    print(
        f"Selected rows: {len(base_data)}"
    )

    print(
        "Selected buildings:"
        f" {base_data['building_id'].nunique()}"
    )

    for mode in modes:
        simulated = generate_scenario(
            base_data,
            mode,
            seed=args.seed,
        )

        output_path = save_scenario(
            simulated,
            mode,
        )

        summary = scenario_summary(
            simulated
        )

        print()
        print(
            f"Generated {mode} production scenario:"
        )
        print(
            f"  rows: {summary['rows']}"
        )
        print(
            f"  buildings: {summary['buildings']}"
        )
        print(
            "  air_temperature_mean:"
            f" {summary['air_temperature_mean']:.3f}"
        )
        print(
            "  dew_temperature_mean:"
            f" {summary['dew_temperature_mean']:.3f}"
        )
        print(
            "  wind_speed_mean:"
            f" {summary['wind_speed_mean']:.3f}"
        )
        print(
            "  target_next_hour_kwh_mean:"
            f" {summary['target_next_hour_kwh_mean']:.3f}"
        )
        print(
            f"  output: {output_path}"
        )


if __name__ == "__main__":
    main()