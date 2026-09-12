from __future__ import annotations

from pathlib import Path
import sys

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.config import phase1_config  # noqa: E402
from ml.evaluation.error_analysis import (  # noqa: E402
    grouped_error,
    residual_table,
)
from ml.evaluation.split import (  # noqa: E402
    temporal_split,
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
        / "hist_gradient_boosting_phase1.joblib"
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

    test["prediction"] = (
        artifact["model"].predict(
            test[
                artifact[
                    "feature_columns"
                ]
            ]
        )
    )

    residuals = residual_table(
        test,
        cfg.target_name,
        "prediction",
    )

    output_dir = (
        cfg.reports_root
        / "error_analysis"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    residuals.to_parquet(
        output_dir
        / "residuals.parquet",
        index=False,
    )

    for group_column in [
        "building_id",
        "hour",
        "weekpart",
        "month",
    ]:
        report = grouped_error(
            residuals,
            group_column,
        )

        report.to_csv(
            output_dir
            / f"by_{group_column}.csv",
            index=False,
        )

    print(
        "Error analysis written to:",
        output_dir,
    )


if __name__ == "__main__":
    main()