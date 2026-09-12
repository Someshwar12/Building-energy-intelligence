from __future__ import annotations

from pathlib import Path
import sys

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.config import phase1_config  # noqa: E402
from ml.evaluation.split import temporal_split  # noqa: E402


def grouped_comparison(
    df: pd.DataFrame,
    group_column: str,
) -> pd.DataFrame:
    rows = []

    for group_value, group in df.groupby(group_column, dropna=False):
        actual = group["actual"]
        rf_error = group["rf_prediction"] - actual
        persistence_error = group["persistence_prediction"] - actual

        rf_mae = rf_error.abs().mean()
        persistence_mae = persistence_error.abs().mean()

        rows.append(
            {
                group_column: group_value,
                "observations": len(group),
                "rf_mae": rf_mae,
                "persistence_mae": persistence_mae,
                "rf_minus_persistence_mae": (
                    rf_mae - persistence_mae
                ),
                "rf_better": rf_mae < persistence_mae,
            }
        )

    return pd.DataFrame(rows).sort_values(
        group_column
    )


def main() -> None:
    cfg = phase1_config(
        ROOT / "configs/project.yaml"
    )

    features_path = (
        cfg.processed_root
        / "phase1_features.parquet"
    )

    model_path = (
        ROOT
        / "models"
        / "random_forest_phase1.joblib"
    )

    if not features_path.exists():
        raise FileNotFoundError(
            "Features file does not exist. "
            "Run phase1_build_features.py first."
        )

    if not model_path.exists():
        raise FileNotFoundError(
            "Model artifact does not exist. "
            "Run phase1_train.py first."
        )

    df = pd.read_parquet(
        features_path
    )

    splits = temporal_split(
        df,
        train_start=cfg.train_start,
        train_end=cfg.train_end,
        validation_start=cfg.validation_start,
        validation_end=cfg.validation_end,
        test_start=cfg.test_start,
        test_end=cfg.test_end,
    )

    test = splits["test"].copy()

    artifact = joblib.load(
        model_path
    )

    test["rf_prediction"] = (
        artifact["model"].predict(
            test[
                artifact[
                    "feature_columns"
                ]
            ]
        )
    )

    test["persistence_prediction"] = (
        test.groupby("building_id")[
            "energy_kwh"
        ].shift(0)
    )

    test["actual"] = test[cfg.target_name]

    comparison = test[
        [
            "timestamp",
            "building_id",
            "hour",
            "month",
            "is_weekend",
            "actual",
            "rf_prediction",
            "persistence_prediction",
        ]
    ].copy()

    comparison["weekpart"] = comparison[
    "is_weekend"
    ].astype(bool).map(
        {
            True: "weekend",
            False: "weekday",
        }
    )

    comparison["rf_residual"] = (
        comparison["rf_prediction"]
        - comparison["actual"]
    )

    comparison["persistence_residual"] = (
        comparison["persistence_prediction"]
        - comparison["actual"]
    )

    comparison = comparison.dropna(
        subset=[
            "actual",
            "rf_prediction",
            "persistence_prediction",
        ]
    )

    output_dir = (
        cfg.reports_root
        / "error_analysis"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    comparison.to_parquet(
        output_dir / "rf_vs_persistence_residuals.parquet",
        index=False,
    )

    for group_column in [
        "building_id",
        "hour",
        "month",
        "weekpart",
    ]:
        report = grouped_comparison(
            comparison,
            group_column,
        )

        report.to_csv(
            output_dir
            / f"rf_vs_persistence_by_{group_column}.csv",
            index=False,
        )

    overall = pd.DataFrame(
        [
            {
                "model": "random_forest",
                "mae": (
                    comparison["rf_residual"]
                    .abs()
                    .mean()
                ),
            },
            {
                "model": "persistence",
                "mae": (
                    comparison[
                        "persistence_residual"
                    ]
                    .abs()
                    .mean()
                ),
            },
        ]
    )

    overall.to_csv(
        output_dir
        / "rf_vs_persistence_overall.csv",
        index=False,
    )

    print(
        "RF vs persistence error analysis written to:",
        output_dir,
    )


if __name__ == "__main__":
    main()