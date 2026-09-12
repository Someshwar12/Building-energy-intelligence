from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.config import (  # noqa: E402
    load_project_config,
    phase1_config,
)
from ml.evaluation.baselines import (  # noqa: E402
    add_baselines,
)
from ml.evaluation.metrics import (  # noqa: E402
    evaluate,
)
from ml.evaluation.split import (  # noqa: E402
    temporal_split,
)
from ml.training.models import (  # noqa: E402
    make_hist_gradient_boosting,
    make_random_forest,
    make_ridge,
)
from ml.training.train import (  # noqa: E402
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

    for spec in models:
        print(
            f"\nTraining: {spec.name}"
        )

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
            "project": "Building & Energy Intelligence Platform",
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
            "validation_metrics": validation_metrics,
            "test_metrics": test_metrics,
        }

        save_artifact(
            spec,
            models_dir
            / f"{spec.name}_phase1.joblib",
            artifact_metadata,
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