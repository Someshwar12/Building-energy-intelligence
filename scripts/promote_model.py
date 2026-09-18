from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

import mlflow
import pandas as pd
from mlflow import MlflowClient

from ml.evaluation.baselines import add_baselines
from ml.evaluation.metrics import evaluate

ROOT = Path(__file__).resolve().parents[1]

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)

REGISTERED_MODEL_NAME = "building-energy-forecast"

PRODUCTION_ALIAS = "production"

RETRAINING_EXPERIMENT_NAME = (
    "building-energy-retraining"
)

EVALUATED_STATUS = "evaluated"

VALIDATION_FRACTION = 0.25

PRODUCTION_DATA_ROOT = (
    ROOT
    / "data"
    / "interim"
    / "production"
)


@dataclass(frozen=True)
class EvaluatedCandidate:
    version: int
    model_family: str
    run_id: str
    candidate_nmae: float
    production_nmae: float | None
    persistence_nmae: float
    beats_production: bool | None
    beats_persistence: bool


def load_production_data(
    mode: str,
) -> pd.DataFrame:
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

    required = {
        "building_id",
        "timestamp",
        "energy_kwh",
        "target_next_hour_kwh",
    }

    missing = sorted(
        required - set(data.columns)
    )

    if missing:
        raise ValueError(
            "Production data is missing required "
            f"columns: {', '.join(missing)}"
        )

    data["timestamp"] = pd.to_datetime(
        data["timestamp"]
    )

    return (
        data
        .sort_values(
            ["building_id", "timestamp"]
        )
        .reset_index(drop=True)
    )


def split_evaluation_window(
    data: pd.DataFrame,
) -> pd.DataFrame:
    split_point = int(
        len(data) * (1.0 - VALIDATION_FRACTION)
    )

    if split_point <= 0:
        raise ValueError(
            "Production dataset is too small for "
            "candidate evaluation."
        )

    validation = data.iloc[
        split_point:
    ].copy()

    if validation.empty:
        raise ValueError(
            "Candidate evaluation window is empty."
        )

    return validation


def get_retraining_experiment_id(
    client: MlflowClient,
) -> str:
    experiment = client.get_experiment_by_name(
        RETRAINING_EXPERIMENT_NAME
    )

    if experiment is None:
        raise RuntimeError(
            "MLflow retraining experiment was not found: "
            f"{RETRAINING_EXPERIMENT_NAME}"
        )

    return experiment.experiment_id


def get_candidate_versions(
    client: MlflowClient,
) -> list:
    """
    Discover Phase 6 candidate models from their MLflow
    retraining experiment rather than mutable lifecycle tags.

    This deliberately does not depend on:
      - lifecycle_status
      - lifecycle_stage
      - promotion_status
      - validation_status
      - phase model-version tags

    Those are mutable lifecycle metadata.

    The MLflow experiment associated with the candidate run
    is the durable provenance boundary separating Phase 6
    retraining candidates from the historical Phase 1 models.
    """

    retraining_experiment_id = (
        get_retraining_experiment_id(client)
    )

    versions = list(
        client.search_model_versions(
            f"name='{REGISTERED_MODEL_NAME}'"
        )
    )

    candidates = []

    for version in versions:
        run_id = version.run_id

        if not run_id:
            continue

        run = client.get_run(run_id)

        if (
            run.info.experiment_id
            != retraining_experiment_id
        ):
            continue

        candidates.append(version)

    candidates.sort(
        key=lambda version: int(
            version.version
        )
    )

    return candidates


def get_production_version(
    client: MlflowClient,
):
    registered_model = client.get_registered_model(
        REGISTERED_MODEL_NAME
    )

    production_version = (
        registered_model.aliases.get(
            PRODUCTION_ALIAS
        )
    )

    if production_version is None:
        return None

    return client.get_model_version(
        REGISTERED_MODEL_NAME,
        str(production_version),
    )


def load_registered_model(
    version: int | str,
):
    model_uri = (
        f"models:/{REGISTERED_MODEL_NAME}/{version}"
    )

    return mlflow.pyfunc.load_model(
        model_uri
    )


def evaluate_model(
    model,
    data: pd.DataFrame,
    feature_columns: list[str],
    prediction_name: str,
) -> dict:
    prediction = model.predict(
        data[feature_columns]
    )

    evaluation = data.copy()

    evaluation[prediction_name] = (
        prediction
    )

    return evaluate(
        evaluation,
        "target_next_hour_kwh",
        prediction_name,
    )


def get_model_feature_columns(
    client: MlflowClient,
    version: int | str,
) -> list[str]:
    model_version = client.get_model_version(
        REGISTERED_MODEL_NAME,
        str(version),
    )

    run = client.get_run(
        model_version.run_id
    )

    features_json = run.data.tags.get(
        "feature_columns"
    )

    if features_json:
        import json

        return json.loads(features_json)

    model_uri = (
        f"models:/{REGISTERED_MODEL_NAME}/{version}"
    )

    model_info = mlflow.models.get_model_info(
        model_uri
    )

    signature = model_info.signature

    if signature is None or signature.inputs is None:
        raise ValueError(
            f"No feature signature found for model v{version}."
        )

    return [
        input_spec.name
        for input_spec in signature.inputs.inputs
        if input_spec.name is not None
    ]


def set_candidate_tag(
    client: MlflowClient,
    version: int,
    key: str,
    value: str,
) -> None:
    client.set_model_version_tag(
        REGISTERED_MODEL_NAME,
        str(version),
        key,
        value,
    )


def evaluate_candidates(
    client: MlflowClient,
    data: pd.DataFrame,
) -> list[EvaluatedCandidate]:
    evaluation_data = (
        split_evaluation_window(data)
    )

    contextual = add_baselines(
        data
    )

    baseline_validation = contextual.loc[
        evaluation_data.index
    ].copy()

    persistence_metrics = evaluate(
        baseline_validation,
        "target_next_hour_kwh",
        "pred_persistence",
    )

    persistence_nmae = float(
        persistence_metrics[
            "macro_building_nmae"
        ]
    )

    production_version = (
        get_production_version(client)
    )

    production_model = None
    production_nmae = None

    if production_version is not None:
        production_model = load_registered_model(
            production_version.version
        )

        production_features = (
            get_model_feature_columns(
                client,
                production_version.version,
            )
        )

        production_metrics = evaluate_model(
            production_model,
            evaluation_data,
            production_features,
            "pred_production",
        )

        production_nmae = float(
            production_metrics[
                "macro_building_nmae"
            ]
        )

    candidates = get_candidate_versions(
        client
    )

    if not candidates:
        raise RuntimeError(
            "No registered candidate models were found "
            f"in MLflow experiment "
            f"'{RETRAINING_EXPERIMENT_NAME}'."
        )

    results: list[EvaluatedCandidate] = []

    for version in candidates:
        model = load_registered_model(
            version.version
        )

        feature_columns = (
            get_model_feature_columns(
                client,
                version.version,
            )
        )

        metrics = evaluate_model(
            model,
            evaluation_data,
            feature_columns,
            "pred_candidate",
        )

        candidate_nmae = float(
            metrics[
                "macro_building_nmae"
            ]
        )

        beats_production = (
            None
            if production_nmae is None
            else candidate_nmae
            < production_nmae
        )

        beats_persistence = (
            candidate_nmae
            < persistence_nmae
        )

        set_candidate_tag(
            client,
            int(version.version),
            "validation_status",
            EVALUATED_STATUS,
        )

        set_candidate_tag(
            client,
            int(version.version),
            "evaluation_window",
            "simulated_production",
        )

        set_candidate_tag(
            client,
            int(version.version),
            "evaluation_metric",
            "macro_building_nmae",
        )

        set_candidate_tag(
            client,
            int(version.version),
            "candidate_nmae",
            f"{candidate_nmae:.6f}",
        )

        set_candidate_tag(
            client,
            int(version.version),
            "persistence_nmae",
            f"{persistence_nmae:.6f}",
        )

        if production_nmae is not None:
            set_candidate_tag(
                client,
                int(version.version),
                "production_nmae",
                f"{production_nmae:.6f}",
            )

        set_candidate_tag(
            client,
            int(version.version),
            "beats_persistence",
            str(
                beats_persistence
            ).lower(),
        )

        if beats_production is not None:
            set_candidate_tag(
                client,
                int(version.version),
                "beats_production",
                str(
                    beats_production
                ).lower(),
            )

        results.append(
            EvaluatedCandidate(
                version=int(
                    version.version
                ),
                model_family=version.tags.get(
                    "model_family",
                    "unknown",
                ),
                run_id=version.run_id,
                candidate_nmae=candidate_nmae,
                production_nmae=production_nmae,
                persistence_nmae=persistence_nmae,
                beats_production=beats_production,
                beats_persistence=beats_persistence,
            )
        )

    return results


def print_evaluation(
    results: list[EvaluatedCandidate],
) -> None:
    print()
    print("=" * 90)
    print("PHASE 6 CANDIDATE EVALUATION")
    print("=" * 90)

    print()

    for result in results:
        production_value = (
            "N/A"
            if result.production_nmae is None
            else f"{result.production_nmae:.6f}"
        )

        print(
            f"v{result.version}"
            f" | {result.model_family}"
            f" | candidate NMAE="
            f"{result.candidate_nmae:.6f}"
            f" | production NMAE="
            f"{production_value}"
            f" | persistence NMAE="
            f"{result.persistence_nmae:.6f}"
            f" | beats production="
            f"{result.beats_production}"
            f" | beats persistence="
            f"{result.beats_persistence}"
        )


def apply_decisions(
    client: MlflowClient,
    results: list[EvaluatedCandidate],
    approve_version: int | None,
) -> None:
    production_version = (
        get_production_version(client)
    )

    current_production = (
        None
        if production_version is None
        else int(
            production_version.version
        )
    )

    for result in results:
        passes_production_gate = (
            result.beats_production is True
            or current_production is None
        )

        passes_persistence_gate = (
            result.beats_persistence
        )

        eligible_for_promotion = (
            passes_production_gate
            and passes_persistence_gate
        )

        if (
            approve_version is not None
            and result.version == approve_version
        ):
            if not eligible_for_promotion:
                raise RuntimeError(
                    f"v{result.version} was explicitly "
                    "selected for promotion but failed "
                    "one or more promotion gates."
                )

            set_candidate_tag(
                client,
                result.version,
                "lifecycle_status",
                "production",
            )

            set_candidate_tag(
                client,
                result.version,
                "promotion_status",
                "approved",
            )

            set_candidate_tag(
                client,
                result.version,
                "promotion_reason",
                (
                    "Candidate passed production and "
                    "persistence evaluation gates and "
                    "received explicit promotion approval."
                ),
            )

            client.set_registered_model_alias(
                REGISTERED_MODEL_NAME,
                PRODUCTION_ALIAS,
                result.version,
            )

            print()
            print(
                f"PROMOTED v{result.version} "
                f"({result.model_family})"
            )

            continue

        if eligible_for_promotion:
            set_candidate_tag(
                client,
                result.version,
                "promotion_status",
                "awaiting_approval",
            )

            set_candidate_tag(
                client,
                result.version,
                "promotion_reason",
                (
                    "Candidate passed evaluation gates "
                    "but requires explicit approval."
                ),
            )

            print()
            print(
                f"v{result.version} "
                f"({result.model_family}) "
                "passed promotion gates and is "
                "awaiting explicit approval."
            )

        else:
            set_candidate_tag(
                client,
                result.version,
                "lifecycle_status",
                "rejected",
            )

            set_candidate_tag(
                client,
                result.version,
                "promotion_status",
                "rejected",
            )

            rejection_reasons = []

            if not passes_production_gate:
                rejection_reasons.append(
                    "candidate did not beat production"
                )

            if not passes_persistence_gate:
                rejection_reasons.append(
                    "candidate did not beat persistence"
                )

            if current_production is None:
                rejection_reasons.append(
                    "no learned production model currently exists"
                )

            set_candidate_tag(
                client,
                result.version,
                "rejection_reason",
                "; ".join(
                    rejection_reasons
                ),
            )

            print()
            print(
                f"v{result.version} "
                f"({result.model_family}) "
                "REJECTED:"
                f" {'; '.join(rejection_reasons)}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate Phase 6 candidates and apply "
            "controlled promotion/rejection gates."
        )
    )

    parser.add_argument(
        "--mode",
        choices=("normal", "shifted"),
        default="shifted",
    )

    parser.add_argument(
        "--approve-version",
        type=int,
        default=None,
        help=(
            "Explicitly approve one evaluated candidate "
            "for production."
        ),
    )

    args = parser.parse_args()

    mlflow.set_tracking_uri(
        MLFLOW_TRACKING_URI
    )

    client = MlflowClient()

    data = load_production_data(
        args.mode
    )

    results = evaluate_candidates(
        client,
        data,
    )

    print_evaluation(results)

    apply_decisions(
        client,
        results,
        args.approve_version,
    )

    print()
    print("=" * 90)
    print("LIFECYCLE DECISION COMPLETE")
    print("=" * 90)

    production = get_production_version(
        client
    )

    if production is None:
        print("Current production: NONE")
    else:
        print(
            "Current production:"
            f" v{production.version}"
            f" ({production.tags.get('model_family', 'unknown')})"
        )


if __name__ == "__main__":
    main()