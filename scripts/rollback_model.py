from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime
from pathlib import Path

import mlflow
from mlflow import MlflowClient

ROOT = Path(__file__).resolve().parents[1]

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)

REGISTERED_MODEL_NAME = "building-energy-forecast"

PRODUCTION_ALIAS = "production"


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


def get_model_version(
    client: MlflowClient,
    version: int,
):
    try:
        return client.get_model_version(
            REGISTERED_MODEL_NAME,
            str(version),
        )
    except Exception as exc:
        raise RuntimeError(
            f"Registered model v{version} was not found."
        ) from exc


def validate_rollback_target(
    client: MlflowClient,
    target_version: int,
    current_version: int | None,
) -> None:
    target = get_model_version(
        client,
        target_version,
    )

    if current_version == target_version:
        raise RuntimeError(
            f"v{target_version} is already the production model."
        )

    if target.status != "READY":
        raise RuntimeError(
            f"Rollback target v{target_version} is not READY."
        )


def set_rollback_tags(
    client: MlflowClient,
    target_version: int,
    previous_version: int | None,
) -> None:
    timestamp = datetime.now(
        UTC
    ).isoformat()

    client.set_model_version_tag(
        REGISTERED_MODEL_NAME,
        str(target_version),
        "lifecycle_status",
        "production",
    )

    client.set_model_version_tag(
        REGISTERED_MODEL_NAME,
        str(target_version),
        "rollback_status",
        "restored",
    )

    client.set_model_version_tag(
        REGISTERED_MODEL_NAME,
        str(target_version),
        "rollback_timestamp",
        timestamp,
    )

    client.set_model_version_tag(
        REGISTERED_MODEL_NAME,
        str(target_version),
        "rollback_from_version",
        (
            "none"
            if previous_version is None
            else str(previous_version)
        ),
    )

    client.set_model_version_tag(
        REGISTERED_MODEL_NAME,
        str(target_version),
        "rollback_reason",
        "Explicit operational rollback to a known model version.",
    )


def rollback(
    client: MlflowClient,
    target_version: int,
) -> None:
    production_version = get_production_version(
        client
    )

    current_version = (
        None
        if production_version is None
        else int(
            production_version.version
        )
    )

    if current_version is None:
        raise RuntimeError(
            "No learned production model currently exists. "
            "Rollback cannot be demonstrated until a production "
            "alias exists."
        )

    validate_rollback_target(
        client,
        target_version,
        current_version,
    )

    set_rollback_tags(
        client,
        target_version,
        current_version,
    )

    client.set_registered_model_alias(
        REGISTERED_MODEL_NAME,
        PRODUCTION_ALIAS,
        target_version,
    )

    print()
    print("=" * 90)
    print("MODEL ROLLBACK COMPLETE")
    print("=" * 90)
    print()
    print(
        f"Previous production: v{current_version}"
    )
    print(
        f"Restored production: v{target_version}"
    )
    print()
    print(
        "Rollback changed the MLflow production alias only."
    )
    print(
        "No retraining or Docker rebuild was performed."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Explicitly roll the MLflow production alias "
            "back to a known registered model version."
        )
    )

    parser.add_argument(
        "--to-version",
        type=int,
        required=True,
        help=(
            "Registered model version to restore as production."
        ),
    )

    args = parser.parse_args()

    mlflow.set_tracking_uri(
        MLFLOW_TRACKING_URI
    )

    client = MlflowClient()

    rollback(
        client,
        args.to_version,
    )


if __name__ == "__main__":
    main()