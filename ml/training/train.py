from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd


def fit_model(
    spec,
    train_df: pd.DataFrame,
    target: str,
):
    target_values = train_df[target]

    valid_target = target_values.notna()

    if valid_target.sum() == 0:
        raise ValueError(
            "No valid target observations in training data."
        )

    spec.pipeline.fit(
        train_df.loc[
            valid_target,
            spec.feature_columns,
        ],
        target_values.loc[valid_target],
    )

    return spec


def predict(
    spec,
    df: pd.DataFrame,
) -> pd.Series:
    predictions = spec.pipeline.predict(
        df[spec.feature_columns]
    )

    return pd.Series(
        predictions,
        index=df.index,
        name=f"pred_{spec.name}",
    )


def save_artifact(
    spec,
    output_path: Path,
    metadata: dict,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact = {
        "model_name": spec.name,
        "model": spec.pipeline,
        "feature_columns": spec.feature_columns,
        "metadata": metadata,
    }

    joblib.dump(
        artifact,
        output_path,
    )


def load_artifact(
    path: Path,
) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Model artifact not found: {path}"
        )

    return joblib.load(path)