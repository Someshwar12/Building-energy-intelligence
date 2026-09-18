from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import mlflow
import pandas as pd
from mlflow import MlflowClient
from mlflow.models import infer_signature

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.config import load_project_config, phase1_config
from ml.evaluation.metrics import evaluate
from ml.training.models import (
    make_hist_gradient_boosting,
    make_random_forest,
    make_ridge,
)
from ml.training.train import fit_model, save_artifact

MLFLOW_EXPERIMENT_NAME = "building-energy-retraining"
MLFLOW_REGISTERED_MODEL_NAME = "building-energy-forecast"

PRODUCTION_DATA_ROOT = (
    ROOT
    / "data"
    / "interim"
    / "production"
)

MODEL_OUTPUT_ROOT = (
    ROOT
    / "models"
    / "candidates"
)

EXCLUDED_FEATURE_COLUMNS = {
    "timestamp",
    "energy_kwh",
    "target_next_hour_kwh",
    "quality_flag",
    "quality_missing",
    "quality_negative",
    "quality_duplicate",
    "simulation_mode",
    "simulation_seed",
}


def get_feature_columns(
    df: pd.DataFrame,
) -> tuple[
    list[str],
    list[str],
    list[str],
]:
    features = [
        column
        for column in df.columns
        if column not in EXCLUDED_FEATURE_COLUMNS
    ]

    categorical = [
        column
        for column in [
            "building_id",
            "site_id",
            "primary_use",
            "timezone",
        ]
        if column in features
    ]

    numeric = [
        column
        for column in features
        if column not in categorical
    ]

    return (
        features,
        numeric,
        categorical,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def get_git_commit() -> str:
    try:
        return subprocess.check_output(
            [
                "git",
                "rev-parse",
                "HEAD",
            ],
            cwd=ROOT,
            text=True,
        ).strip()
    except (
        OSError,
        subprocess.CalledProcessError,
    ):
        return "unknown"


def build_models(
    raw_config: dict,
    features: list[str],
    numeric: list[str],
    categorical: list[str],
    seed: int,
):
    model_config = raw_config[
        "phase1"
    ]["models"]

    return [
        make_ridge(
            features,
            numeric,
            categorical,
            alpha=model_config[
                "ridge"
            ]["alpha"],
        ),
        make_random_forest(
            features,
            numeric,
            categorical,
            n_estimators=model_config[
                "random_forest"
            ]["n_estimators"],
            max_depth=model_config[
                "random_forest"
            ]["max_depth"],
            min_samples_leaf=model_config[
                "random_forest"
            ]["min_samples_leaf"],
            n_jobs=model_config[
                "random_forest"
            ]["n_jobs"],
            seed=seed,
        ),
        make_hist_gradient_boosting(
            features,
            numeric,
            categorical,
            learning_rate=model_config[
                "hist_gradient_boosting"
            ]["learning_rate"],
            max_iter=model_config[
                "hist_gradient_boosting"
            ]["max_iter"],
            max_leaf_nodes=model_config[
                "hist_gradient_boosting"
            ]["max_leaf_nodes"],
            l2_regularization=model_config[
                "hist_gradient_boosting"
            ]["l2_regularization"],
            min_samples_leaf=model_config[
                "hist_gradient_boosting"
            ]["min_samples_leaf"],
            seed=seed,
        ),
    ]


def load_production_data(
    mode: str,
) -> tuple[pd.DataFrame, Path]:
    path = (
        PRODUCTION_DATA_ROOT
        / f"{mode}_production.parquet"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Production simulation file not found: {path}"
        )

    data = pd.read_parquet(path)

    if data.empty:
        raise ValueError(
            f"Production simulation file is empty: {path}"
        )

    return data, path


def validate_candidate_data(
    data: pd.DataFrame,
) -> None:
    required = {
        "building_id",
        "timestamp",
        "target_next_hour_kwh",
    }

    missing = sorted(
        required - set(data.columns)
    )

    if missing:
        raise ValueError(
            "Candidate training data is missing "
            f"required columns: {', '.join(missing)}"
        )

    if data["target_next_hour_kwh"].isna().all():
        raise ValueError(
            "Candidate training data contains no valid "
            "target observations."
        )

    if (
        data["target_next_hour_kwh"].dropna() < 0
    ).any():
        raise ValueError(
            "Candidate training data contains negative "
            "target values."
        )


def log_candidate_configuration(
    *,
    model_name: str,
    cfg,
    features: list[str],
    numeric: list[str],
    categorical: list[str],
    data: pd.DataFrame,
    training_data: pd.DataFrame,
    validation_data: pd.DataFrame,
    source_path: Path,
    source_mode: str,
) -> None:
    mlflow.log_params(
        {
            "model_name": model_name,
            "target": cfg.target_name,
            "horizon_hours": cfg.horizon_hours,
            "seed": cfg.seed,
            "candidate_rows": len(data),
            "training_rows": len(training_data),
            "validation_rows": len(validation_data),
            "feature_count": len(features),
            "numeric_feature_count": len(numeric),
            "categorical_feature_count": len(
                categorical
            ),
            "source_mode": source_mode,
            "source_sha256": sha256_file(
                source_path
            ),
        }
    )

    mlflow.set_tags(
        {
            "project": (
                "building-energy-intelligence"
            ),
            "phase": "phase6",
            "lifecycle_stage": "candidate",
            "source_mode": source_mode,
            "git_commit": get_git_commit(),
        }
    )

    mlflow.log_dict(
        {
            "features": features,
            "numeric_features": numeric,
            "categorical_features": categorical,
            "excluded_features": sorted(
                EXCLUDED_FEATURE_COLUMNS
            ),
        },
        "configuration/features.json",
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Train controlled MLflow candidate models "
            "from simulated production data."
        )
    )

    parser.add_argument(
        "--mode",
        choices=("normal", "shifted"),
        default="shifted",
    )

    args = parser.parse_args()

    raw_config = load_project_config(
        ROOT / "configs/project.yaml"
    )

    cfg = phase1_config(
        ROOT / "configs/project.yaml"
    )

    data, source_path = load_production_data(
        args.mode
    )

    validate_candidate_data(data)

    data["timestamp"] = pd.to_datetime(
        data["timestamp"]
    )

    data = data.sort_values(
        ["building_id", "timestamp"]
    ).reset_index(drop=True)

    # The simulated production window is treated as a
    # chronological candidate-training dataset.
    split_point = int(
        len(data) * 0.75
    )

    training_data = data.iloc[
        :split_point
    ].copy()

    validation_data = data.iloc[
        split_point:
    ].copy()

    (
        features,
        numeric,
        categorical,
    ) = get_feature_columns(data)

    models = build_models(
        raw_config,
        features,
        numeric,
        categorical,
        cfg.seed,
    )

    mlflow_tracking_uri = os.getenv(
        "MLFLOW_TRACKING_URI",
        "http://127.0.0.1:5000",
    )

    mlflow.set_tracking_uri(
        mlflow_tracking_uri
    )

    mlflow.set_experiment(
        MLFLOW_EXPERIMENT_NAME
    )

    mlflow_client = MlflowClient()

    MODEL_OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        f"Candidate training source: {source_path}"
    )
    print(
        f"Candidate mode: {args.mode}"
    )
    print(
        f"Training rows: {len(training_data)}"
    )
    print(
        f"Validation rows: {len(validation_data)}"
    )

    for spec in models:
        print(
            f"\nTraining candidate: {spec.name}"
        )

        with mlflow.start_run(
            run_name=(
                f"{spec.name}-"
                f"phase6-{args.mode}-candidate"
            )
        ):
            fit_model(
                spec,
                training_data,
                cfg.target_name,
            )

            predictions = spec.pipeline.predict(
                validation_data[
                    spec.feature_columns
                ]
            )

            validation = validation_data.copy()

            validation[
                f"pred_{spec.name}"
            ] = predictions

            validation_metrics = evaluate(
                validation,
                cfg.target_name,
                f"pred_{spec.name}",
            )

            artifact_metadata = {
                "project": (
                    "Building & Energy "
                    "Intelligence Platform"
                ),
                "phase": "phase6",
                "lifecycle_stage": "candidate",
                "source_mode": args.mode,
                "source_path": str(
                    source_path
                ),
                "source_sha256": sha256_file(
                    source_path
                ),
                "model_name": spec.name,
                "target": cfg.target_name,
                "horizon_hours": cfg.horizon_hours,
                "feature_columns": features,
                "seed": cfg.seed,
                "validation_metrics": (
                    validation_metrics
                ),
            }

            artifact_path = (
                MODEL_OUTPUT_ROOT
                / (
                    f"{spec.name}_"
                    f"{args.mode}_candidate.joblib"
                )
            )

            save_artifact(
                spec,
                artifact_path,
                artifact_metadata,
            )

            mlflow.log_metrics(
                {
                    f"validation_{key}": float(
                        value
                    )
                    for key, value
                    in validation_metrics.items()
                }
            )

            mlflow.log_params(
                {
                    "candidate_model_family": (
                        spec.name
                    ),
                    "candidate_source_mode": (
                        args.mode
                    ),
                }
            )

            mlflow.log_artifact(
                str(artifact_path),
                artifact_path="candidate_model",
            )

            mlflow.log_artifact(
                str(source_path),
                artifact_path="candidate_data",
            )

            model_input = training_data[
                features
            ].head(5).copy()

            model_output = (
                spec.pipeline.predict(
                    model_input
                )
            )

            signature = infer_signature(
                model_input,
                model_output,
            )

            model_info = mlflow.sklearn.log_model(
                sk_model=spec.pipeline,
                name="candidate_model",
                signature=signature,
                input_example=model_input,
                registered_model_name=(
                    MLFLOW_REGISTERED_MODEL_NAME
                ),
                skops_trusted_types=[
                    "numpy.dtype",
                ],
                metadata={
                    "model_name": spec.name,
                    "phase": "phase6",
                    "lifecycle_stage": "candidate",
                    "source_mode": args.mode,
                    "git_commit": get_git_commit(),
                    "feature_columns": features,
                },
            )

            registered_version = (
                model_info.registered_model_version
            )

            if registered_version is None:
                raise RuntimeError(
                    "Candidate model was logged "
                    "but was not registered."
                )

            mlflow_client.set_model_version_tag(
                MLFLOW_REGISTERED_MODEL_NAME,
                str(registered_version),
                "model_family",
                spec.name,
            )

            mlflow_client.set_model_version_tag(
                MLFLOW_REGISTERED_MODEL_NAME,
                str(registered_version),
                "validation_status",
                "candidate",
            )

            mlflow_client.set_model_version_tag(
                MLFLOW_REGISTERED_MODEL_NAME,
                str(registered_version),
                "lifecycle_status",
                "candidate",
            )

            mlflow_client.set_model_version_tag(
                MLFLOW_REGISTERED_MODEL_NAME,
                str(registered_version),
                "source_mode",
                args.mode,
            )

            print(
                "MLflow run:",
                mlflow.active_run().info.run_id,
            )

            print(
                "Registered candidate:",
                MLFLOW_REGISTERED_MODEL_NAME,
                "version:",
                registered_version,
            )


if __name__ == "__main__":
    main()