from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import mlflow
import pandas as pd
from mlflow import MlflowClient

ROOT = Path(__file__).resolve().parents[1]

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)

REGISTERED_MODEL_NAME = "building-energy-forecast"

VALIDATION_METRIC = "validation_macro_building_nmae"

BASELINE_RESULTS_PATH = (
    ROOT / "reports" / "generated" / "phase1_baseline_results.csv"
)

CANDIDATE_ALIAS = "candidate"
PRODUCTION_ALIAS = "production"


@dataclass(frozen=True)
class ModelCandidate:
    version: int
    model_family: str
    validation_metric: float
    run_id: str


def get_best_baseline() -> tuple[str, float]:
    if not BASELINE_RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Baseline results not found: {BASELINE_RESULTS_PATH}"
        )

    baseline_df = pd.read_csv(BASELINE_RESULTS_PATH)

    required_columns = {"baseline", "macro_building_nmae"}

    missing_columns = required_columns.difference(
        baseline_df.columns
    )

    if missing_columns:
        raise ValueError(
            "Baseline results are missing required columns: "
            f"{sorted(missing_columns)}"
        )

    baseline_df = baseline_df.dropna(
        subset=["baseline", "macro_building_nmae"]
    )

    if baseline_df.empty:
        raise ValueError(
            "Baseline results contain no valid macro-building "
            "NMAE observations."
        )

    best = baseline_df.sort_values(
        "macro_building_nmae"
    ).iloc[0]

    return (
        str(best["baseline"]),
        float(best["macro_building_nmae"]),
    )


def get_evaluated_models(
    client: MlflowClient,
) -> list[ModelCandidate]:
    versions = list(
        client.search_model_versions(
            f"name='{REGISTERED_MODEL_NAME}'"
        )
    )

    candidates: list[ModelCandidate] = []

    for version in versions:
        if version.tags.get("validation_status") != "evaluated":
            continue

        model_family = version.tags.get(
            "model_family",
            "unknown",
        )

        run = client.get_run(version.run_id)

        metric = run.data.metrics.get(
            VALIDATION_METRIC
        )

        if metric is None:
            continue

        candidates.append(
            ModelCandidate(
                version=int(version.version),
                model_family=model_family,
                validation_metric=float(metric),
                run_id=version.run_id,
            )
        )

    return candidates


def clear_alias_if_present(
    client: MlflowClient,
    alias: str,
) -> None:
    aliases = client.get_registered_model(
        REGISTERED_MODEL_NAME
    ).aliases

    if alias in aliases:
        client.delete_registered_model_alias(
            REGISTERED_MODEL_NAME,
            alias,
        )


def main() -> None:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    client = MlflowClient()

    models = get_evaluated_models(client)

    if not models:
        raise RuntimeError(
            "No evaluated registered model versions "
            "with the required validation metric were found."
        )

    models.sort(
        key=lambda model: model.validation_metric
    )

    best_ml_model = models[0]

    baseline_name, baseline_metric = get_best_baseline()

    improvement_pct = (
        (baseline_metric - best_ml_model.validation_metric)
        / baseline_metric
        * 100.0
    )

    print()
    print("=" * 80)
    print("MODEL PROMOTION GUARD")
    print("=" * 80)

    print()
    print("Evaluated learned models:")

    for model in models:
        print(
            f"  v{model.version}"
            f" | {model.model_family}"
            f" | {VALIDATION_METRIC}="
            f"{model.validation_metric:.6f}"
        )

    print()
    print(
        f"Best learned model: "
        f"v{best_ml_model.version} "
        f"({best_ml_model.model_family})"
    )

    print(
        f"Best learned-model validation NMAE: "
        f"{best_ml_model.validation_metric:.6f}"
    )

    print()
    print(f"Baseline: {baseline_name}")

    print(
        f"Baseline validation NMAE: "
        f"{baseline_metric:.6f}"
    )

    print()
    print(
        f"Relative improvement vs baseline: "
        f"{improvement_pct:.2f}%"
    )

    if best_ml_model.validation_metric < baseline_metric:
        print()
        print("BASELINE GUARD: PASSED")
        print(
            "The learned model improves on the "
            "persistence baseline."
        )

        client.set_model_version_tag(
            REGISTERED_MODEL_NAME,
            str(best_ml_model.version),
            "lifecycle_status",
            "production",
        )

        client.set_model_version_tag(
            REGISTERED_MODEL_NAME,
            str(best_ml_model.version),
            "baseline_guard",
            "passed",
        )

        client.set_model_version_tag(
            REGISTERED_MODEL_NAME,
            str(best_ml_model.version),
            "baseline_model",
            baseline_name,
        )

        client.set_model_version_tag(
            REGISTERED_MODEL_NAME,
            str(best_ml_model.version),
            "baseline_validation_nmae",
            f"{baseline_metric:.6f}",
        )

        client.set_model_version_tag(
            REGISTERED_MODEL_NAME,
            str(best_ml_model.version),
            "promotion_metric",
            VALIDATION_METRIC,
        )

        clear_alias_if_present(
            client,
            CANDIDATE_ALIAS,
        )

        client.set_registered_model_alias(
            REGISTERED_MODEL_NAME,
            PRODUCTION_ALIAS,
            best_ml_model.version,
        )

        print(
            f"Assigned @{PRODUCTION_ALIAS} "
            f"-> v{best_ml_model.version}"
        )

    else:
        print()
        print("BASELINE GUARD: FAILED")
        print(
            "No learned model is allowed to become production "
            "because the persistence baseline remains better."
        )

        client.set_model_version_tag(
            REGISTERED_MODEL_NAME,
            str(best_ml_model.version),
            "lifecycle_status",
            "rejected",
        )

        client.set_model_version_tag(
            REGISTERED_MODEL_NAME,
            str(best_ml_model.version),
            "baseline_guard",
            "failed",
        )

        client.set_model_version_tag(
            REGISTERED_MODEL_NAME,
            str(best_ml_model.version),
            "baseline_model",
            baseline_name,
        )

        client.set_model_version_tag(
            REGISTERED_MODEL_NAME,
            str(best_ml_model.version),
            "baseline_validation_nmae",
            f"{baseline_metric:.6f}",
        )

        client.set_model_version_tag(
            REGISTERED_MODEL_NAME,
            str(best_ml_model.version),
            "rejection_reason",
            (
                "Learned model did not beat the "
                "persistence baseline on validation "
                "macro-building NMAE."
            ),
        )

        clear_alias_if_present(
            client,
            CANDIDATE_ALIAS,
        )

        print(
            f"Removed @{CANDIDATE_ALIAS} because "
            f"v{best_ml_model.version} failed the guard."
        )

        print(
            f"@{PRODUCTION_ALIAS} was NOT changed."
        )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()