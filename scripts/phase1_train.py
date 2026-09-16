from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import mlflow
import pandas as pd
import sklearn
from mlflow import MlflowClient
from mlflow.models import infer_signature

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.config import (
    load_project_config,
    phase1_config,
)
from ml.evaluation.baselines import (
    add_baselines,
)
from ml.evaluation.metrics import (
    evaluate,
)
from ml.evaluation.split import (
    temporal_split,
)
from ml.training.models import (
    make_hist_gradient_boosting,
    make_random_forest,
    make_ridge,
)
from ml.training.train import (
    fit_model,
    predict,
    save_artifact,
)

EXCLUDED_FEATURE_COLUMNS = {
    "timestamp",
    "energy_kwh",
    "target_next_hour_kwh",
    "quality_flag",
    "quality_missing",
    "quality_negative",
    "quality_duplicate",
}

MLFLOW_EXPERIMENT_NAME = "building-energy-phase1"
MLFLOW_REGISTERED_MODEL_NAME = "building-energy-forecast"


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


def log_training_configuration(
    *,
    raw_config: dict,
    cfg,
    spec,
    features: list[str],
    numeric: list[str],
    categorical: list[str],
    df: pd.DataFrame,
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    features_path: Path,
) -> None:
    dataset_hash = sha256_file(features_path)

    mlflow.log_params(
        {
            "model_name": spec.name,
            "target": cfg.target_name,
            "horizon_hours": cfg.horizon_hours,
            "seed": cfg.seed,
            "dataset_rows": len(df),
            "feature_count": len(features),
            "numeric_feature_count": len(numeric),
            "categorical_feature_count": len(
                categorical
            ),
            "train_rows": len(train),
            "validation_rows": len(validation),
            "test_rows": len(test),
            "dataset_sha256": dataset_hash,
            "train_start": str(cfg.train_start),
            "train_end": str(cfg.train_end),
            "validation_start": str(
                cfg.validation_start
            ),
            "validation_end": str(
                cfg.validation_end
            ),
            "test_start": str(cfg.test_start),
            "test_end": str(cfg.test_end),
        }
    )

    mlflow.set_tags(
        {
            "project": (
                "building-energy-intelligence"
            ),
            "phase": "phase1",
            "model": spec.name,
            "git_commit": get_git_commit(),
            "python_version": (
                f"{sys.version_info.major}."
                f"{sys.version_info.minor}."
                f"{sys.version_info.micro}"
            ),
            "sklearn_version": sklearn.__version__,
            "mlflow_version": mlflow.__version__,
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

    mlflow.log_dict(
        {
            "numeric": {
                "imputer": "median",
                "scaler": "StandardScaler",
            },
            "categorical": {
                "imputer": "most_frequent",
                "encoder": "OneHotEncoder",
                "handle_unknown": "ignore",
            },
            "remainder": "drop",
        },
        "configuration/preprocessing.json",
    )

    mlflow.log_dict(
        {
            "phase1": {
                "models": raw_config[
                    "phase1"
                ]["models"],
            }
        },
        "configuration/project_config.json",
    )


def log_metrics(
    validation_metrics: dict,
    test_metrics: dict,
) -> None:
    mlflow.log_metrics(
        {
            f"validation_{key}": float(value)
            for key, value in validation_metrics.items()
        }
    )

    mlflow.log_metrics(
        {
            f"test_{key}": float(value)
            for key, value in test_metrics.items()
        }
    )


def main() -> None:
    raw_config = load_project_config(
        ROOT / "configs/project.yaml"
    )

    cfg = phase1_config(
        ROOT / "configs/project.yaml"
    )

    features_path = (
        cfg.processed_root
        / "phase1_features.parquet"
    )

    if not features_path.exists():
        raise FileNotFoundError(
            "Phase 1 feature dataset does not exist.\n"
            "Run phase1_build_features.py first."
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

    train = splits["train"]

    # Compute baselines on the complete chronological dataset.
    # Then select validation/test rows.
    contextual = add_baselines(df)

    validation = contextual.loc[
        splits["validation"].index
    ].copy()

    test = contextual.loc[
        splits["test"].index
    ].copy()

    (
        features,
        numeric,
        categorical,
    ) = get_feature_columns(df)

    model_config = raw_config[
        "phase1"
    ]["models"]

    models = [
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
            seed=cfg.seed,
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
            seed=cfg.seed,
        ),
    ]

    model_results: list[dict] = []

    models_dir = ROOT / "models"

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

    for spec in models:
        print(
            f"\nTraining: {spec.name}"
        )

        with mlflow.start_run(
            run_name=f"{spec.name}-phase1"
        ):
            fit_model(
                spec,
                train,
                cfg.target_name,
            )

            validation[
                f"pred_{spec.name}"
            ] = predict(
                spec,
                validation,
            )

            test[
                f"pred_{spec.name}"
            ] = predict(
                spec,
                test,
            )

            validation_metrics = evaluate(
                validation,
                cfg.target_name,
                f"pred_{spec.name}",
            )

            test_metrics = evaluate(
                test,
                cfg.target_name,
                f"pred_{spec.name}",
            )

            model_results.append(
                {
                    "model": spec.name,
                    **{
                        f"validation_{key}": value
                        for key, value
                        in validation_metrics.items()
                    },
                    **{
                        f"test_{key}": value
                        for key, value
                        in test_metrics.items()
                    },
                }
            )

            artifact_metadata = {
                "project": (
                    "Building & Energy "
                    "Intelligence Platform"
                ),
                "phase": "phase1",
                "model_name": spec.name,
                "target": cfg.target_name,
                "horizon_hours": cfg.horizon_hours,
                "training_window": [
                    cfg.train_start,
                    cfg.train_end,
                ],
                "validation_window": [
                    cfg.validation_start,
                    cfg.validation_end,
                ],
                "test_window": [
                    cfg.test_start,
                    cfg.test_end,
                ],
                "feature_columns": features,
                "seed": cfg.seed,
                "validation_metrics": (
                    validation_metrics
                ),
                "test_metrics": test_metrics,
            }

            artifact_path = (
                models_dir
                / f"{spec.name}_phase1.joblib"
            )

            save_artifact(
                spec,
                artifact_path,
                artifact_metadata,
            )

            log_training_configuration(
                raw_config=raw_config,
                cfg=cfg,
                spec=spec,
                features=features,
                numeric=numeric,
                categorical=categorical,
                df=df,
                train=train,
                validation=validation,
                test=test,
                features_path=features_path,
            )

            mlflow.log_params(
                {
                    f"model_config_{key}": str(
                        value
                    )
                    for key, value in model_config[
                        spec.name
                    ].items()
                }
            )

            log_metrics(
                validation_metrics,
                test_metrics,
            )

            mlflow.log_artifact(
                str(artifact_path),
                artifact_path="model",
            )

            mlflow.log_artifact(
                str(
                    ROOT
                    / "configs/project.yaml"
                ),
                artifact_path="configuration",
            )

            model_input = train[
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
                name="mlflow_model",
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
                    "phase": "phase1",
                    "target": cfg.target_name,
                    "horizon_hours": str(
                        cfg.horizon_hours
                    ),
                    "git_commit": get_git_commit(),
                    "feature_columns": features,
                },
            )

            registered_version = (
                model_info.registered_model_version
            )

            if registered_version is None:
                raise RuntimeError(
                    "MLflow model was logged "
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
                "evaluated",
            )

            print(
                "MLflow run:",
                mlflow.active_run().info.run_id,
            )

            print(
                "Registered model:",
                MLFLOW_REGISTERED_MODEL_NAME,
                "version:",
                registered_version,
            )

    reports_dir = cfg.reports_root

    reports_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_results_df = (
        pd.DataFrame(model_results)
        .sort_values(
            "validation_macro_building_nmae"
        )
    )

    model_results_df.to_csv(
        reports_dir / "phase1_model_results.csv",
        index=False,
    )

    baseline_results = []

    for baseline_name in [
        "pred_persistence",
        "pred_previous_day",
        "pred_previous_week",
    ]:
        baseline_results.append(
            {
                "baseline": baseline_name,
                **evaluate(
                    test,
                    cfg.target_name,
                    baseline_name,
                ),
            }
        )

    baseline_results_df = (
        pd.DataFrame(baseline_results)
        .sort_values(
            "macro_building_nmae"
        )
    )

    baseline_results_df.to_csv(
        reports_dir / "phase1_baseline_results.csv",
        index=False,
    )

    print("\nMODEL RESULTS")
    print("=" * 90)
    print(
        model_results_df.to_string(
            index=False
        )
    )

    print("\nBASELINE RESULTS")
    print("=" * 90)
    print(
        baseline_results_df.to_string(
            index=False
        )
    )

    print(
        "\nArtifacts saved to:",
        models_dir,
    )


if __name__ == "__main__":
    main()